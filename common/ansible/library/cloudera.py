#!/usr/bin/python
# -*- coding: utf-8 -*-

import httplib
import base64
import json
import time
from functools import partial
from cm_api.api_client import ApiResource
from cm_api.endpoints.services import ApiServiceSetupInfo
from cm_api.api_client import ApiException
from ansible.module_utils.basic import AnsibleModule


def waitUntilPositive(function):
    while not function():
        time.sleep(5)


class Log:

    ERROR = 0
    WARN = 1
    INFO = 2
    DEBUG = 3
    TRACE = 4
    __level = ERROR
    __loggers = []

    def __init__(self, level, loggers):
        self.__level = level
        self.__loggers = loggers

    def error(self, msg):
        if self.__level >= Log.ERROR:
            self.log(msg)

    def info(self, msg):
        if self.__level >= Log.INFO:
            self.log(msg)

    def log(self, msg):
        for logger in self.__loggers:
            if logger == 'sys.stdout':
                print timedStr(str(msg))
            else:
                fw = open(logger, 'a+')
                fw.write(timedStr(str(msg) + '\n'))


def timedStr(mesg):
    return '[' + str(time.strftime('%Y%m%d.%H%M%S')) + '] ' + mesg


class ClouderaUtils:

    def __init__(self, module):
        self.module = module
        self.cloudera_api_version = 11
        self.cloudera_server = module.params['cloudera_server']
        self.encoded_config_map = module.params['encoded_config_map']
        self.encoded_parcels_map = module.params['encoded_parcels_map']
        self.encoded_service_config = module.params['encoded_service_config']
        self.encoded_role_config = module.params['encoded_role_config']
        self.cluster_name = module.params['cluster_name']
        self.service_name = module.params['service_name']
        self.service_type = module.params['service_type']
        self.role_name = module.params['role_name']
        self.role_type = module.params['role_type']
        self.command = module.params['command']
        self.cdh_version = module.params['cdh_version']
        self.spark2_version = module.params['spark2_version']
        self.hosts = module.params['hosts']
        self._logger_name = 'ClouderaUtils'
        self.logfile = Log(Log.INFO, ['/tmp/ansible_log.txt'])
        self.logout = Log(Log.INFO, ['sys.stdout'])

    def begin_trial(self):
        self.logfile.info('Beginning cloudera trial')
        try:
            auth = base64.encodestring('%s:%s' % ('admin', 'admin')).replace('\n', '')
            httpMethod = 'POST'
            httpPage = '/api/v%d/cm/trial/begin' % self.cloudera_api_version
            conn = httplib.HTTPConnection(self.cloudera_server + ':7180')
            header = {'Authorization': 'Basic ' + auth}
            conn.request(httpMethod, httpPage, '', header)
            resp = conn.getresponse()
            responseText = resp.read()

            if resp.status == 204:
                self.logfile.info('Output: Status 204: ' + responseText)
                result = (True, '')
            else:
                responseText = str(resp.status) + ' ' + str(resp.reason) + ' ' + str(responseText)
                self.logfile.info('Output: Status<>204: ' + responseText)
                result = (False, responseText)
        # pylint: disable=W0703
        except Exception, e:
            result = (False, str(e))
        return result

    def put_config(self):
        self.logfile.info('Putting cloudera config')
        try:
            configs = json.loads(base64.b64decode(self.encoded_config_map))
            configdata = {'items': []}
            for key in configs:
                configdata['items'].append({'name': key, 'value': configs[key]})
            auth = base64.encodestring('%s:%s' % ('admin', 'admin')).replace('\n', '')
            httpMethod = 'PUT'
            httpPage = '/api/v%d/cm/config' % self.cloudera_api_version
            conn = httplib.HTTPConnection(self.cloudera_server + ':7180')
            header = {'Authorization': 'Basic ' + auth, 'Content-Type': 'application/json'}
            data = json.dumps(configdata)
            self.logfile.info(data)
            conn.request(httpMethod, httpPage, data, header)
            resp = conn.getresponse()
            output = resp.read()
            self.logfile.info('Output: ' + output)
            if resp.status == 200:
                result = (True, json.loads(output))
            else:
                result = (False, str(resp.status) + ' ' + str(resp.reason) + ' ' + str(output))
        # pylint: disable=W0703
        except Exception, e:
            result = (False, str(e))
        return result

    def test(self):
        result = (True, 'Test passed')
        return result

    def deploy_management_service(self):
        self.logfile.info('Starting deploy_management_service')
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        manager = api.get_cloudera_manager()
        mgmt = manager.create_mgmt_service(ApiServiceSetupInfo())
        mgmt.create_role('SERVICEMONITOR-1', 'SERVICEMONITOR', self.cloudera_server)
        mgmt.create_role('EVENTSERVER-1', 'EVENTSERVER', self.cloudera_server)
        mgmt.create_role('HOSTMONITOR-1', 'HOSTMONITOR', self.cloudera_server)
        mgmt.create_role('ALERTPUBLISHER-1', 'ALERTPUBLISHER', self.cloudera_server)
        mgmt.create_role('REPORTSMANAGER-1', 'REPORTSMANAGER', self.cloudera_server)
        for group in mgmt.get_all_role_config_groups():
            if group.roleType == 'SERVICEMONITOR':
                group.update_config({})
            if group.roleType == 'EVENTSERVER':
                group.update_config({'event_server_heapsize': '215964392'})
            if group.roleType == 'HOSTMONITOR':
                group.update_config({})
            if group.roleType == 'ALERTPUBLISHER':
                group.update_config({})
            if group.roleType == 'REPORTSMANAGER':
                group.update_config({
                    'headlamp_database_host': self.cloudera_server + ':7432',
                    'headlamp_database_user': 'rman',
                    'headlamp_database_password': 'YMg9wKyXfI',
                    'headlamp_database_type': 'postgresql',
                    'headlamp_database_name': 'rman',
                    'headlamp_heapsize': '268435456',
                })
        self.logfile.info('Waiting deploy_management_service')
        mgmt.start().wait()
        self.logfile.info('Completed deploy_management_service')
        result = (True, '')
        return result

    def create_cluster(self):
        self.logfile.info('Started create_cluster')
        self.logfile.info('Setting parcel repo')
        self.set_parcel_repo(self.cdh_version, "CDH")
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        self.logfile.info('CDH version:' + self.cdh_version)
        cluster = api.create_cluster(self.cluster_name, fullVersion=self.cdh_version)
        self.logfile.info('Adding hosts...')
        cluster.add_hosts(self.hosts)
        self.logfile.info('Completed create_cluster')
        result = (True, '')
        return result

    def set_parcel_repo(self, version, parcel_name):
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        if parcel_name == "CDH":
            parcel_repo = 'http://archive.cloudera.com/cdh5/parcels/' + version + '/'
        elif parcel_name == "SPARK2":
            parcel_repo = 'http://archive.cloudera.com/spark2/parcels/' + version + '.0.cloudera1/'
        cm_config = api.get_cloudera_manager().get_config(view='full')
        repo_config = cm_config['REMOTE_PARCEL_REPO_URLS']
        value = repo_config.value or repo_config.default
        # value is a comma-separated list
        value += ',' + parcel_repo
        api.get_cloudera_manager().update_config({
            'REMOTE_PARCEL_REPO_URLS': value})
        # wait to make sure parcels are refreshed
        time.sleep(30)
        self.logfile.info('Completed to set parcel repo for %s %s' % (parcel_name, version))
        result = (True, '')
        return result

    def get_full_version(self, version, product):
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        cparcels = cluster.get_all_parcels()
        self.logfile.info("----")
        for parcel in cparcels:
            self.logfile.info(parcel)
            if parcel.product == product and parcel.version.startswith(version):
                return parcel.version
        self.logfile.info("----")
        return '0'

    def remove_parcel_for_product(self, product):
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        cparcels = cluster.get_all_parcels()
        for parcel in cparcels:
            if parcel.product == product:
                parcel.deactivate().wait()
                parcel.start_removal_of_distribution().wait()
        result = (True, '')
        return result

    def get_vora_version(self):
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        cparcels = cluster.get_all_parcels()
        for parcel in cparcels:
            if parcel.product == 'SAPHanaVora':
                return parcel.version
        return '0'

    def deploy_parcels(self):
        self.logfile.info('Starting deploy_parcels')
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        self.logfile.info(self.encoded_parcels_map)
        parcels = json.loads(base64.b64decode(self.encoded_parcels_map))
        self.logfile.info(parcels)
        for parcel in parcels:
            self.logfile.info(parcel)
            if parcel['name'] == 'CDH':
                version = self.get_full_version(self.cdh_version, 'CDH')
            elif parcel['name'] == 'SAPHanaVora':
                version = self.get_vora_version()
            elif parcel['name'] == 'SPARK2':
                version = self.get_full_version(self.spark2_version, 'SPARK2')
            else:
                version = parcel['version']
            self.logfile.info('Getting parcel: ' + parcel['name'] + 'with version: ' + version + ' ...')
            p = cluster.get_parcel(parcel['name'], version)
            p.start_download()
            while True:
                p = cluster.get_parcel(parcel['name'], version)
                if p.stage == 'DOWNLOADED':
                    break
                if p.state.errors:
                    raise Exception(str(p.state.errors))
                self.logfile.info('Downloading %s: %s / %s' % (parcel['name'], p.state.progress, p.state.totalProgress))
                time.sleep(15)
            self.logfile.info('Downloaded %s' % parcel['name'])
            p.start_distribution()
            while True:
                p = cluster.get_parcel(parcel['name'], version)
                if p.stage == 'DISTRIBUTED':
                    break
                if p.state.errors:
                    raise Exception(str(p.state.errors))
                self.logfile.info('Distributing %s: %s / %s' % (parcel['name'], p.state.progress, p.state.totalProgress))
                time.sleep(15)
            self.logfile.info('Distributed %s' % parcel['name'])
            p.activate()
            while True:
                p = cluster.get_parcel(parcel['name'], version)
                if p.stage == 'ACTIVATED':
                    break
                if p.state.errors:
                    raise Exception(str(p.state.errors))
                self.logfile.info('Activating %s: %s / %s' % (parcel['name'], p.state.progress, p.state.totalProgress))
                time.sleep(15)
            self.logfile.info('Activated %s' % parcel['name'])
        result = (True, '')
        return result

    def create_service(self):
        self.logfile.info('Starting create_service')
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        self.logfile.info('Creating service: ' + self.service_name + ' service_type: ' + self.service_type)
        service = cluster.create_service(self.service_name, self.service_type)
        self.logfile.info('with json config: ' + base64.b64decode(self.encoded_service_config))
        service_config = json.loads(base64.b64decode(self.encoded_service_config))
        self.logfile.info('with config: ' + str(service_config))
        service.update_config(service_config)
        result = (True, '')
        return result

    def delete_service(self):
        self.logfile.info('Starting delete_service')
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        self.logfile.info('Deleting service: ' + self.service_name)
        cluster.delete_service(self.service_name)
        self.logfile.info('Service deleted: ' + self.service_name)
        result = (True, '')
        return result

    def create_role(self):
        self.logfile.info('Starting create_role')
        if len(self.hosts) != 1:
            result = (False, 'Only 1 host should be passed, you passed ' + str(len(self.hosts)) + ' hosts')
            return result
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        self.logfile.info('Getting service: ' + self.service_name)
        service = cluster.get_service(self.service_name)
        self.logfile.info('Create role: ' + self.role_name + ' type: ' + self.role_type + ' hosts: ' + ','.join(self.hosts))
        role = service.create_role(self.role_name, self.role_type, self.hosts[0])
        if self.encoded_role_config is not None:
            self.logfile.info('config: ' + self.encoded_role_config)
            role_config = json.loads(base64.b64decode(self.encoded_role_config))
            self.logfile.info('decoded_config: ' + str(role_config))
            role.update_config(role_config)
        else:
            self.logfile.info('no configuration ')
        self.logfile.info('Completed create_role')
        result = (True, '')
        return result

    def execute_service_command(self):
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        service = cluster.get_service(self.service_name)
        # pylint: disable=W0212
        service._cmd(self.command)
        result = (True, '')
        return result

    def format_hdfs(self):
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        service = cluster.get_service(self.service_name)
        service.format_hdfs(self.role_name)[0].wait()
        result = (True, '')
        return result

    def restart_cluster(self):
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        cluster.stop().wait()
        cluster.start().wait()
        result = (True, '')
        return result

    def deploy_client_config(self):
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        cluster.deploy_client_config().wait()
        result = (True, '')
        return result

    def check_cluster(self):
        self.logfile.info('Checking if cluster exists for cloudera...')
        for _ in range(0, 3):
            (status, _) = self.get_cluster()
            if not status:
                return False
            else:
                pass
            time.sleep(10)
        return True

    def get_cluster(self):
        self.logfile.info('Getting cluster ' + self.cluster_name + ' from ' + self.cloudera_server)
        try:
            auth = base64.encodestring('%s:%s' % ('admin', 'admin')).replace('\n', '')
            httpMethod = 'GET'
            httpPage = '/api/v%d/clusters/%s' % (self.cloudera_api_version, self.cluster_name)
            conn = httplib.HTTPConnection(self.cloudera_server + ':7180')
            header = {'Authorization': 'Basic ' + auth}
            conn.request(httpMethod, httpPage, '', header)
            resp = conn.getresponse()
            output = resp.read()
            self.logfile.info('Output: ' + output)
            if resp.status == 200:
                result = (True, json.loads(output))
            else:
                result = (False, str(resp.status) + ' ' + str(resp.reason) + ' ' + str(output))
        # pylint: disable=W0703
        except Exception, e:
            self.logfile.info('Exception: ' + str(e))
            result = (False, str(e))
        return result

    def wait_cluster(self):
        waitUntilPositive(partial(self.check_cluster))
        result = (True, '')
        return result

    def start_service(self):
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)
        service = cluster.get_service(self.service_name)
        service.start().wait()
        result = (True, '')
        return result

    def cm_exec_command_and_wait(self, max_retries, msg, command, *args, **kwargs):
        succeeded, response_msg = False, ''
        sleep_sec = kwargs.get("sleep_sec", 10)

        for _ in range(0, max_retries):
            cmd = command(*args)

            succeeded, response_msg = self.cm_wait_command(msg, cmd)

            if succeeded:
                break
            else:
                time.sleep(sleep_sec)

        return succeeded, response_msg

    def cm_wait_command(self, msg, cmd):
        self.logfile.info("Attempting: " + msg)

        cmd.wait()

        while cmd.success is None:
            cmd = cmd.fetch()

        self.logfile.info(msg + " result: Active= " + str(cmd.active) + ", Success= " + str(cmd.success))
        self.logfile.info("ResultMessage: " + cmd.resultMessage)

        return cmd.success, cmd.resultMessage

    def enable_kerberos(self):
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cm = api.get_cloudera_manager()
        cluster = api.get_cluster(self.cluster_name)

        # update security-related configuration
        self.logfile.info("Update security configuration")
        cm.update_config({"KDC_HOST": "master.ansible",
                          "SECURITY_REALM": "ANSIBLE",
                          "KRB_MANAGE_KRB5_CONF": "false",
                          "KRB_ENC_TYPES": "aes256-cts-hmac-sha1-96 arcfour-hmac-md5 des3-hmac-sha1 des-cbc-crc"})

        # import Kerberos admin principals to management server
        krb_admin_princ = self.module.params['cloudera_krb_admin_princ']
        krb_admin_passwd = self.module.params['cloudera_krb_admin_passwd']

        succeeded, msg = self.cm_exec_command_and_wait(1, "Import admin credentials",
                                                       cm.import_admin_credentials,
                                                       krb_admin_princ, krb_admin_passwd)

        if not succeeded:
            return False, msg

        # try to stop cluster
        succeeded, msg = self.cm_exec_command_and_wait(5, "Stop cluster", cluster.stop)

        if not succeeded:
            return False, msg

        # configure Cloudera cluster for Kerberos
        succeeded, msg = self.cm_exec_command_and_wait(1, "Configure Kerberos for cluster",
                                                       cluster.configure_for_kerberos,
                                                       1004, 1006)

        if not succeeded:
            return False, msg

        # Have Kerberos credentials generated by cloudera manager
        succeeded, msg = self.cm_exec_command_and_wait(5, "Generate missing credentials",
                                                       cm.generate_credentials)

        if not succeeded:
            return False, msg

        # Deploy client configuration
        succeeded, msg = self.cm_exec_command_and_wait(5, "Deploy client configs",
                                                       cluster.deploy_client_config)
        if not succeeded:
            return False, msg

        # try to start cloudera cluster
        succeeded, msg = self.cm_exec_command_and_wait(5, "Start Cluster",
                                                       cluster.start)

        if not succeeded:
            return False, msg
        else:
            return True, ''

    def get_service(self, service_name):
        api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
        cluster = api.get_cluster(self.cluster_name)

        return cluster.get_service(service_name)

    def update_service_config(self, service_name, service_config, append):
        try:
            service = self.get_service(service_name)
            # pylint: disable=W0123
            new_conf_dict = eval(service_config)

            if append:
                for k, v in new_conf_dict.items():
                    old_conf = service.get_config()[0].get(k)

                    if old_conf is not None:
                        new_conf_dict[k] = old_conf + v

            return True, str(service.update_config(new_conf_dict)[0])
        except ApiException as apie:
            return False, str(apie)

    def stop_service(self, service_name):
        try:
            service = self.get_service(service_name)
            api_cmd = service.stop().wait()

            return api_cmd.success, api_cmd.resultMessage
        except ApiException as apie:
            return False, str(apie)

    def restart_service(self, service_name):
        try:
            service = self.get_service(service_name)
            api_cmd = service.restart().wait()

            return api_cmd.success, api_cmd.resultMessage
        except ApiException as apie:
            return False, str(apie)

    def get_service_role_config_group(self, service_name, group_name):
        service = self.get_service(service_name)

        for role_config_group in service.get_all_role_config_groups():
            if role_config_group.name == group_name:
                return role_config_group

        raise ApiException("Role configuration group {0} is not defined in service {1} of cluster {2}".
                           format(group_name, service_name, self.cluster_name))

    @staticmethod
    def merge_values(old, new, sep, key_val_sep):
        if not old:
            return new

        old_conf = dict(map(lambda x: x.split(key_val_sep, 1), old.split(sep)))
        new_conf = dict(map(lambda x: x.split(key_val_sep, 1), new.split(sep)))
        common_conf = [(k, "{0}{1}{2}".format(old_conf[k], key_val_sep, new_conf[k])) for k in
                       set(new_conf) & set(old_conf)]
        result_conf = old_conf.copy()

        result_conf.update(new_conf)
        result_conf.update(common_conf)

        return sep.join(map(key_val_sep.join, result_conf.items()))

    def update_service_role_config(self, service_name, role_name, key, value, append=True,
                                   merge_values=False, sep='\n', key_val_sep=' '):
        try:
            role_config_group = self.get_service_role_config_group(service_name, role_name)
            config_map = role_config_group.get_config(view='full')

            if key not in config_map:
                raise ApiException("Configuration key {0} is not defined for role {1}".
                                   format(key, role_name))

            if append:
                old_val = config_map[key].value

                if merge_values:
                    new_val = ClouderaUtils.merge_values(old_val, value, sep, key_val_sep)
                else:
                    if old_val is None:
                        old_val = ""

                    new_val = "{0}{1}{2}".format(old_val, sep, value)
            else:
                new_val = value

            return True, str(role_config_group.update_config({key: new_val}))
        except ApiException as apie:
            return False, str(apie)

    def restart_management_service(self):
        try:
            self.logfile.info('Starting deploy_management_service')
            api = ApiResource(self.cloudera_server, version=self.cloudera_api_version, username='admin', password='admin')
            mgmt = api.get_cloudera_manager().get_service()
            mgmt.stop().wait()
            mgmt.start().wait()
            return True, ''
        except ApiException as apie:
            return False, str(apie)

def main():
    module = AnsibleModule(argument_spec=dict(
        cloudera_server=dict(default='localhost', type='str'),
        request_type=dict(required=True, choices=[
            'trial',
            'configuration',
            'management_service',
            'cluster',
            'parcels',
            'service',
            'role',
            'client_config',
        ], type='str'),
        request_action=dict(required=True, choices=[
            'wait',
            'create',
            'delete',
            'start',
            'put',
            'deploy',
            'command',
            'format_hdfs',
            'restart',
            'enable_kerberos',
            'config',
            'stop',
            'set_parcel_repo'
        ], type='str'),
        cluster_name=dict(required=False, type='str'),
        service_name=dict(required=False, type='str'),
        service_type=dict(required=False, type='str'),
        role_name=dict(required=False, type='str'),
        role_type=dict(required=False, type='str'),
        command=dict(required=False, type='str'),
        cdh_version=dict(required=False, type='str'),
        spark2_version=dict(required=False, type='str'),
        hosts=dict(required=False, type='list'),
        encoded_config_map=dict(required=False, type='str'),
        encoded_parcels_map=dict(required=False, type='str'),
        encoded_service_config=dict(required=False, type='str'),
        encoded_role_config=dict(required=False, type='str'),
        cloudera_krb_admin_princ=dict(required=False, type='str'),
        cloudera_krb_admin_passwd=dict(required=False, type='str'),
        config_key=dict(required=False, type='str'),
        config_value=dict(required=False, type='str'),
        append=dict(default=True, type='bool'),
        merge_values=dict(default=False, type='bool'),
        separator=dict(default='\n', type='str'),
        key_val_separator=dict(default=' ', type='str'),
        parcel_name=dict(required=False, type='str'),
        parcel_version=dict(required=False, type='str')
    ))

    debug_msg = ''
    cloudera = ClouderaUtils(module)

    if module.params['request_type'] == 'configuration':
        if module.params['request_action'] == 'put':
            (succeeded, msg) = cloudera.put_config()
        elif module.params['request_action'] == 'enable_kerberos':
            (succeeded, msg) = cloudera.enable_kerberos()
        else:
            module.fail_json(msg='Unsupported request action: ' + cloudera.request_action + ' for request type: ' + cloudera.request_type)
    elif module.params['request_type'] == 'trial':
        if module.params['request_action'] == 'start':
            (succeeded, msg) = cloudera.begin_trial()
        else:
            module.fail_json(msg='Unsupported request action: ' + cloudera.request_action + ' for request type: ' + cloudera.request_type)
    elif module.params['request_type'] == 'management_service':
        if module.params['request_action'] == 'deploy':
            (succeeded, msg) = cloudera.deploy_management_service()
        elif module.params['request_action'] == 'restart':
            (succeeded, msg) = cloudera.restart_management_service()
        else:
            module.fail_json(msg='Unsupported request action: ' + cloudera.request_action + ' for request type: ' + cloudera.request_type)
    elif module.params['request_type'] == 'client_config':
        if module.params['request_action'] == 'deploy':
            (succeeded, msg) = cloudera.deploy_client_config()
        else:
            module.fail_json(msg='Unsupported request action: ' + cloudera.request_action + ' for request type: ' + cloudera.request_type)
    elif module.params['request_type'] == 'cluster':
        if module.params['request_action'] == 'create':
            (succeeded, msg) = cloudera.create_cluster()
        elif module.params['request_action'] == 'restart':
            (succeeded, msg) = cloudera.restart_cluster()
        elif module.params['request_action'] == 'wait':
            (succeeded, msg) = cloudera.wait_cluster()
        else:
            module.fail_json(msg='Unsupported request action: ' + cloudera.request_action + ' for request type: ' + cloudera.request_type)
    elif module.params['request_type'] == 'service':
        if module.params['request_action'] == 'create':
            (succeeded, msg) = cloudera.create_service()
        elif module.params['request_action'] == 'delete':
            (succeeded, msg) = cloudera.delete_service()
        elif module.params['request_action'] == 'command':
            (succeeded, msg) = cloudera.execute_service_command()
        elif module.params['request_action'] == 'format_hdfs':
            (succeeded, msg) = cloudera.format_hdfs()
        elif module.params['request_action'] == 'start':
            (succeeded, msg) = cloudera.start_service()
        elif module.params['request_action'] == 'stop':
            (succeeded, msg) = cloudera.stop_service(module.params['service_name'])
        elif module.params['request_action'] == 'config':
            (succeeded, msg) = cloudera.update_service_config(module.params['service_name'],
                                                              base64.b64decode(module.params['encoded_service_config']),
                                                              module.params['append'])
        elif module.params['request_action'] == 'restart':
            (succeeded, msg) = cloudera.restart_service(module.params['service_name'])
        else:
            module.fail_json(msg='Unsupported request action: ' + cloudera.request_action + ' for request type: ' + cloudera.request_type)
    elif module.params['request_type'] == 'role':
        if module.params['request_action'] == 'create':
            (succeeded, msg) = cloudera.create_role()
        elif module.params['request_action'] == 'config':
            (succeeded, msg) = cloudera.update_service_role_config(module.params['service_name'],
                                                                   module.params['role_name'],
                                                                   module.params['config_key'],
                                                                   module.params['config_value'],
                                                                   module.params['append'],
                                                                   module.params['merge_values'],
                                                                   module.params['separator'],
                                                                   module.params['key_val_separator'])
        else:
            module.fail_json(msg='Unsupported request action: ' + cloudera.request_action + ' for request type: ' + cloudera.request_type)
    elif module.params['request_type'] == 'parcels':
        if module.params['request_action'] == 'deploy':
            (succeeded, msg) = cloudera.deploy_parcels()
        elif module.params['request_action'] == 'delete':
            (succeeded, msg) = cloudera.remove_parcel_for_product(module.params['parcel_name'])
        elif module.params['request_action'] == 'set_parcel_repo':
            # here only add url into repo, and you can execute multi times. When deploy, you have to special product name and version again.
            (succeeded, msg) = cloudera.set_parcel_repo(module.params['parcel_version'], module.params['parcel_name'])
        else:
            module.fail_json(msg='Unsupported request action: ' + cloudera.request_action + ' for request type: ' + cloudera.request_type)
    else:
        module.fail_json(msg='Unsupported request type:' + cloudera.request_type)

    if not succeeded:
        module.fail_json(msg=msg)
        return

    result = {}
    result['changed'] = True
    result['response'] = msg
    result['debug'] = debug_msg

    # pylint: disable=W0142
    module.exit_json(**result)


if __name__ == '__main__':
    main()
