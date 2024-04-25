import base64
import json
import uuid
from subprocess import check_output, STDOUT, CalledProcessError
import time
import requests
import sys, os

SYSTEM_NAMESPACE = 'datahub-system'

SERVICE_ID = '740a2273-22be-4fd3-b0e1-1328fd12e98'

def kubectl(args, kubeconfig=None, **kwargs):
    """Run a kubectl command with the given arguments.
    If kubeconfig is provided, it is used to run the command. If not, the
    kubeconfig to use is decided based on kubectl's loading order.
    """
    cmd = ['kubectl']
    if kubeconfig is not None:
        cmd += ['--kubeconfig', kubeconfig]
    cmd += args
    return check_output(cmd, stderr=STDOUT, **kwargs)

def decode_broker_secret(secret_data):
    user = str(base64.b64decode(secret_data['data']['username']), 'utf-8')
    password = str(base64.b64decode(secret_data['data']['password']), 'utf-8')

    return user, password


def generate_tenant_id():
    return str(uuid.uuid1())


def get_basic_auth_credentials(username, password):
    basic_auth = username + ":" + password
    basic_auth_bytes = basic_auth.encode('utf-8')
    base64_bytes = base64.b64encode(basic_auth_bytes)
    return base64_bytes.decode('utf-8')


class SanityChecks:
    #def __init__(self, kubeconfig, plan_id):
    def __init__(self, kubeconfig, plan_id,tenant_id):
        self.kubeconfig = kubeconfig
        self.tenant_id = tenant_id
        broker_proxy_enabled = self.broker_proxy_deployed(SYSTEM_NAMESPACE)
        if broker_proxy_enabled:
            broker_secret_name = 'dis-broker-proxy-creds'
            broker_ingress_name = 'dis-proxy'
            service_name = 'dis-broker-proxy'
            self.airport = '9091'
        else:
            broker_secret_name = 'dis-broker-creds'
            broker_ingress_name = 'dis-ingress'
            service_name = 'dis-broker'
            self.airport = '9090'

        time.sleep(10)
        print('broker_secret_name=' + broker_secret_name)
        broker_username, broker_password = self.get_dis_broker_credentials(broker_secret_name)
        self.broker_basic_auth = get_basic_auth_credentials(broker_username, broker_password)
        print('self.broker_basic_auth=' + self.broker_basic_auth)
        print('broker_username=' + broker_username)
        print('broker_password=' + broker_password)
        self.broker_ingress_url = self.get_ingress_url(broker_ingress_name, SYSTEM_NAMESPACE)

        plan_list = self.get_service_and_plan_id(SERVICE_ID)
        if plan_id not in plan_list:
            print("Fatal error: service plan_id: {} is not registered in service broker or service broker proxy".format(plan_id))
            print("Supported service plan_id: {}".format(plan_list))
            sys.exit(1)

        self.service_id = SERVICE_ID
        self.plan_id = plan_id

    def get_ingress_url(self, ingress_name, namespace):
        """
            Get Ingress URL from DI-E Cluster
        """
        ingress_file = 'ingress_content.json'
        get_url_cmd = 'export KUBECONFIG=' + self.kubeconfig + '&& kubectl get ingress ' + ingress_name + ' -n ' + namespace + ' -o json' + ' 1>' + ingress_file +' 2>/dev/null'
        os.system(get_url_cmd)
        if os.path.isfile(ingress_file):
            ingress_content =json.load(open('ingress_content.json','r'))
        else:
            print('can not get ingress url, exit')
            sys.exit(1)

        return "https://{}".format(ingress_content['spec']['rules'][0]['host'])

    def port_url(self, service_name,  namespace):
        """
           Port forward the url to localhost
        """
        service_port = 'svc/' + service_name + ' ' + self.airport + ':8080'

        cmd_broker = 'export KUBECONFIG=' + self.kubeconfig + '&&kubectl port-forward ' + service_port + ' -n ' + namespace + ' > /dev/null &'
        os.system(cmd_broker)
        cmd_system = 'export KUBECONFIG=' + self.kubeconfig + '&&kubectl port-forward svc/vsystem 8797:8797 -n datahub > /dev/null &'

    def get_dis_broker_credentials(self, broker_secret_name):
        """
            Get system credentials from secret
        """
        secret = json.loads(
            kubectl(['get', 'secret', broker_secret_name, '-n', 'datahub-system', '-o=jsonpath={.data}',
                     '-o', 'json'], kubeconfig=self.kubeconfig))

        return decode_broker_secret(secret)

    def get_service_and_plan_id(self, service_id):
        headers = {
            'X-Broker-API-Version': '2.15',
            'Authorization': 'Basic ' + self.broker_basic_auth,
        }
        url = "{}/v2/catalog".format(self.broker_ingress_url)

        resp = requests.get(url, headers=headers)
        if not resp.ok:
            raise RuntimeError("Request to {} failed with: {}".format(url,resp.reason))

        plan_list = []
        for service in resp.json()['services']:
            if service['id'] == service_id and service['plans']:
                for plan in service['plans']:
                    plan_list.append(plan['id'])

        return plan_list

    def create_tenant(self):
        service_type = os.getenv("SERVICE_PLAN","")

        if service_type and (service_type.endswith('HC') or service_type.endswith('CCM')):
            data = {
                "service_id": self.service_id,
                "plan_id": self.plan_id,
                "parameters": {
                    "tenantId": self.tenant_id,
                    "runtimeCapacity": 0
                }
            }

        else:
            data = {
                "service_id": self.service_id,
                "plan_id": self.plan_id,
                "parameters": {
                    "tenantId": self.tenant_id,
                    "tenantUaaUrl": "https://orcastarkiller.com",
                }
            }

        print(str(data))
        headers = {
            'Content-Type': 'application/json',
            'X-Broker-API-Version': '2.15',
            'Authorization': 'Basic ' + self.broker_basic_auth,
        }
        url = "{}/v2/service_instances/{}?accepts_incomplete=true".format(
            self.broker_ingress_url, self.tenant_id)

        print("Sending request for tenant {} creation...".format(self.tenant_id))
        resp = requests.put(url, headers=headers, json=data)
        if not resp.ok:
            raise RuntimeError("Request to {} failed with: {}".format(url,resp.reason))
        print("Request successfully sent")

    def delete_tenant(self):
        headers = {
            'X-Broker-API-Version': '2.15',
            'Authorization': 'Basic ' + self.broker_basic_auth,
        }
        url = "{}/v2/service_instances/{}?accepts_incomplete=true&service_id={}&plan_id={}".format(
            self.broker_ingress_url, self.tenant_id, self.service_id, self.plan_id)

        print("Sending request for tenant {} deletion...".format(self.tenant_id))
        resp = requests.delete(url, headers=headers)
        if not resp.ok:
            raise RuntimeError("Request to {} failed with: {}".format(url,resp.reason))
        print("Request successfully sent")

    def check_tenant_state(self, operation):
        headers = {
            'X-Broker-API-Version': '2.15',
            'Authorization': 'Basic ' + self.broker_basic_auth,
        }
        url = "{}/v2/service_instances/{}/last_operation?service_id={}&plan_id={}&operation={}".format(
            self.broker_ingress_url, self.tenant_id, self.service_id, self.plan_id, operation)

        resp = requests.get(url, headers=headers)
        if not resp.ok:
            raise RuntimeError("Request to {} failed with: {}".format(url,resp.reason))

        return resp.json()

    def get_tenant_credentials(self):
        data = {
            "service_id": self.service_id,
            "plan_id": self.plan_id,
        }
        headers = {
            'Content-Type': 'application/json',
            'X-Broker-API-Version': '2.15',
            'Authorization': 'Basic ' + self.broker_basic_auth,
        }
        url = "{}/v2/service_instances/{}/service_bindings/dis-service-key".format(
            self.broker_ingress_url, self.tenant_id)

        print("Fetching tenant {} credentials...".format(self.tenant_id))
        resp = requests.put(url, headers=headers, json=data)
        if not resp.ok:
            raise RuntimeError("Request to {} failed with: {}".format(url, resp.reason))

        username = resp.json()['credentials']['username']
        password = resp.json()['credentials']['password']
        vsystem_url = resp.json()['credentials']['url']
        return username, password, vsystem_url

    def login_and_get_user(self, env_file):
        username, password, vsystem_url = self.get_tenant_credentials()
        print(vsystem_url)
        username = username.split('\\')[1]
        system_user, system_password = self.system_tenant()
        vctl_tenant='vctl login ' + vsystem_url + ' ' + self.tenant_id + ' ' + username + ' -p \'' +  password + '\'' + ' --insecure'
        print(vctl_tenant)
        tenant_result = os.system(vctl_tenant)

        vctl_system='vctl login ' + vsystem_url + ' system ' + system_user + ' -p \'' +  system_password + '\'' + ' --insecure'
        print(vctl_system)
        system_result = os.system(vctl_system)

        if tenant_result != 0:
            print('DI:E tenant can not be login with vctl')
            return False
        if system_result != 0:
            print('DI:E system tenant can not be login with vctl')
            return False

        TENANT_ID = ''
        vctl_tenant_info_cmd="vctl util http -X GET '/api/tenant-management/v3/tenants/" + self.tenant_id + "'"
        print(vctl_tenant_info_cmd)
        r = os.popen(vctl_tenant_info_cmd)
        tenant_info = r.read()
        print(tenant_info)
        tenant_info = eval(tenant_info)
        r.close()
        if tenant_info and 'id' in tenant_info.keys():
            TENANT_ID=tenant_info['id']

        line = '\n' + 'export VSYSTEM_ENDPOINT=' + vsystem_url + '\n' + 'export VORA_SYSTEM_TENANT=system \n' + 'export VORA_USERNAME=' + username + '\n' + 'export VORA_PASSWORD=\'' + password + '\'\n' + 'export VORA_TENANT=' + self.tenant_id + '\n' + 'export TENANT_NAME=' + self.tenant_id + '\n' + 'export TENANT_ID=' + TENANT_ID + '\n' + 'export VORA_SYSTEM_USERNAME=' + system_user + '\n' + 'export VORA_SYSTEM_TENANT_PASSWORD=\'' + system_password + '\'\n' + 'export KUBECONFIG=' + self.kubeconfig + '\n'

        with open(env_file, 'a') as fp:
            fp.write(line)
        fp.close()

        return True

    def system_tenant(self):
        secret = json.loads(
            kubectl(['get', 'secret/vora.conf.initial.user', '-n', 'datahub', '-o=jsonpath={.data}',
                     '-o', 'json'], kubeconfig=self.kubeconfig))

        return decode_broker_secret(secret)

        '''
        headers = {
            'Authorization': 'Basic ' + get_basic_auth_credentials(username, password),
        }
        url = "{}/auth/v2/user".format(vsystem_url)

        resp = requests.get(url, headers=headers)
        if not resp.ok:
            raise RuntimeError("Request to {} failed with: {}".format(url, resp.reason))

        user = resp.json()
        expected_user = {
            "tenant": self.tenant_id,
            "username": "dis-user",
            "role": "member",
            "active": True,
            "apiVersion": "v2"
        }
        assert_that(user[0]['username']).equals(expected_user['username'])
        assert_that(user[0]['tenant']).equals(expected_user['tenant'])
        print("Credentials successfully validated")
        '''

    def tenant_was_created(self):
        wait_time = 0
        while True:
           resp = self.check_tenant_state("provision")

           if resp['state'] == 'succeeded':
               print(self.tenant_id + ' creation successfully')
               break
           else:
               if wait_time < 1200:
                   print(self.tenant_id + ' creation still in progress...')
                   time.sleep(30)
                   wait_time += 30
               else:
                   print(self.tenant_id + ' creation failed even wait for 600m')
                   return False
        return True

    def tenant_was_deleted(self):
        wait_time = 0
        while True:
            resp = self.check_tenant_state("deprovision")

            if resp['state'] == 'succeeded':
                print(self.tenant_id + ' deletion successfully')
                break
            else:
                if wait_time < 600:
                   print(self.tenant_id + ' deletion still in progress...')
                   time.sleep(30)
                   wait_time += 30
                else:
                   print(self.tenant_id + ' deletion failed even wait for 600m')
                   return False
        return True

    def broker_proxy_deployed(self, namespace):
        """
        check if service broker proxy deployed or not
        """
        broker_proxy_name = 'dis-broker-proxy'
        try:
            kubectl(['get', 'deployment', broker_proxy_name, '-n', namespace], kubeconfig=self.kubeconfig)
        except CalledProcessError as e:
            expected_error = "deployments.apps " + {} + " not found".format(broker_proxy_name)
            if expected_error in e.output.decode("utf-8"):
                return False
            else:
                raise

        return True

