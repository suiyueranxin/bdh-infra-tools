#!/usr/bin/python

import httplib
import base64
import json
import time
from functools import partial
from ansible.module_utils.basic import AnsibleModule


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


def waitUntilPositive(function):
    (completed, succeeded) = function()
    while not completed:
        time.sleep(5)
        (completed, succeeded) = function()

    return succeeded


class AmbariUtils:
    logfile = Log(Log.INFO, ['/tmp/ansible_log.txt'])
    logout = Log(Log.INFO, ['sys.stdout'])

    HTTP_GET = "GET"
    HTTP_POST = "POST"
    HTTP_PUT = "PUT"
    HTTP_DELETE = "DELETE"

    HTTP_OK = 200

    RESTAPI_EMPTY_PAYLOAD = None
    RESTAPI_INSTALL_SERVICE = json.dumps({"ServiceInfo": {"state": "INSTALLED"}})
    RESTAPI_START_SERVICE = json.dumps({"ServiceInfo": {"state": "STARTED"}})
    RESTAPI_STOP_ALL_INSTALLED = json.dumps({"RequestInfo": {"context": "Stop Service"},
                                             "Body": {"ServiceInfo": {"state": "INSTALLED"}}})

    NAME_SERVICE_KERBEROS = "KERBEROS"
    NAME_COMPONENT_KERBEROS_CLI = "KERBEROS_CLIENT"
    NAME_ARTIFACT_KRB_DESCRIPTOR = "kerberos_descriptor"

    def __init__(self, module):
        self.module = module
        self.ambari_server = module.params['ambari_server']
        self.cluster_name = module.params['cluster_name']

    def install_service(self, service_name):
        return self.add_service(AmbariUtils.HTTP_PUT, service_name, AmbariUtils.RESTAPI_INSTALL_SERVICE)

    def uninstall_service(self, service_name):
        return self.add_service(AmbariUtils.HTTP_DELETE, service_name, AmbariUtils.RESTAPI_INSTALL_SERVICE)

    @classmethod
    def get_request(self, ambari_server, cluster_name, request_id):
        # log = logging.getLogger(self._logger_name)
        # log.debug('Getting request "%s" for cluster "%s" from ambari server "%s"', request_id, cluster_name, ambari_server)
        try:
            auth = base64.encodestring('%s:%s' % (
                'admin', 'admin')).replace('\n', '')
            httpMethod = 'GET'
            httpPage = '/api/v1/clusters/' + cluster_name + '/requests/' + request_id
            conn = httplib.HTTPConnection(ambari_server + ':8080')
            header = {"Authorization": "Basic " + auth,
                      "X-Requested-By": "ambari"
                      }
            sendData = ''
            # log.debug('Prepared request: %s %s %s %s', httpMethod, httpPage, sendData, header)
            conn.request(httpMethod, httpPage, sendData, header)
            resp = conn.getresponse()
            output = resp.read()
            # log.debug('Response status: %d reason: %s text: %s' , resp.status, resp.reason, output)
            if resp.status == 200:
                result = (True, json.loads(output))
            else:
                result = (False, str(resp.status) + ' ' +
                          str(resp.reason) + ' ' + str(output))
        # pylint: disable=W0703
        except Exception as e:
            # log.debug(str(e))
            result = (False, str(e))
        return result

    @classmethod
    def check_request_completed(self, ambari_server, cluster_name, request_id):
        # log = logging.getLogger(self._logger_name)
        # log.debug('Checking request "%s" is comleted for cluster "%s" in ambari server "%s"', request_id, cluster_name, ambari_server)
        for _ in range(0, 3):
            (status, response) = AmbariUtils.get_request(ambari_server, cluster_name, request_id)
            if not status:
                self.logfile.info('check_request_completed: not completed status false, return false,false')
                return False, False  # (completed?, succeeded?)
            else:
                if response['Requests']['request_status'] != 'COMPLETED' and response['Requests']['request_status'] != 'FAILED' and response['Requests']['request_status'] != 'TIMEDOUT':
                    self.logfile.info('check_request_completed: not COMPLETED or FAILED or TIMEDOUT, return false,false')
                    return False, False
            time.sleep(1)

        if response['Requests']['request_status'] == 'COMPLETED':
            self.logfile.info('check_request_completed: completed, return true,true')
            return (True, True)
        else:
            self.logfile.info('check_request_completed: completed but failed, return true,false')
            return (True, False)

    def get_endpoint_stack_repo(self, stack_name, stack_version, operating_system, repo_id):
        return "stacks/{0}/versions/{1}/operating_systems/{2}/repositories/{3}".format(stack_name, stack_version,
                                                                                       operating_system, repo_id)

    def get_endpoint_cluster(self):
        return "clusters/%s" % self.cluster_name

    def get_endpoint_services(self):
        return "%s/services" % self.get_endpoint_cluster()

    def get_endpoint_configurations(self):
        return "%s/configurations" % self.get_endpoint_cluster()

    def get_endpoint_desired_configs(self):
        return "%s?fields=Clusters/desired_configs" % self.get_endpoint_cluster()

    def get_endpoint_service_config_versions(self):
        return "%s/service_config_versions" % self.get_endpoint_configurations()

    def get_endpoint_configurations_for_type_tag(self, config_type, config_tag):
        return "{0}?type={1}&tag={2}".format(self.get_endpoint_configurations(), config_type, config_tag)

    def get_endpoint_service(self, service_name):
        return "{0}/{1}".format(self.get_endpoint_services(), service_name)

    def get_endpoint_cluster_artifact(self, artifact_name):
        return "{0}/artifacts/{1}".format(self.get_endpoint_cluster(), artifact_name)

    def get_endpoint_service_component(self, service_name, component_name):
        return "{0}/components/{1}".format(self.get_endpoint_service(service_name), component_name)

    def get_endpoint_host(self, host):
        return "{0}/hosts?Hosts/host_name={1}".format(self.get_endpoint_cluster(), host)

    def get_endpoint_service_config(self, config_name, tag):
        return "{0}?type={1}&tag={2}".format(self.get_endpoint_configurations(), config_name, tag)

    class ApiResponse:
        def __init__(self, succeeded, msg, resp_code, debug_msg="", content=None):
            self.succeeded = succeeded
            self.msg = msg
            self.resp_code = resp_code
            self.debug_msg = debug_msg
            self.debug_mode = self.debug_msg is not ""
            self.content = content

    class ApiException(Exception):
        def __init__(self, api_response):
            super(AmbariUtils.ApiException, self).__init__(api_response.msg)

            self.api_response = api_response
            self.api_response.succeeded = False

    def ambari_api_call(self, http_method, api_endpoint, payload=RESTAPI_EMPTY_PAYLOAD, debug_mode=False):
        if debug_mode:
            debug_msg = payload
        else:
            debug_msg = ""

        try:
            auth = base64.encodestring('%s:%s' % (
                'admin', 'admin')).replace('\n', '')
            url = '/api/v1/' + api_endpoint
            conn = httplib.HTTPConnection(self.ambari_server + ':8080')
            header = {"Authorization": "Basic " + auth,
                      "X-Requested-By": "ambari"
                      }
            # log.debug('Prepared request: %s %s %s %s', httpMethod, httpPage, sendData, header)
            conn.request(http_method, url, payload, header)
            resp = conn.getresponse()
            output = resp.read()

            # log.debug('Response status: %d reason: %s text: %s' , resp.status, resp.reason, output)
            if resp.status == 200 or resp.status == 201:
                result = AmbariUtils.ApiResponse(True, "{0} {1}".format(resp.status, resp.reason),
                                                 resp.status, debug_msg, output)
            elif resp.status == 202:
                resp_body = json.loads(output)
                request_id = str(resp_body['Requests']['id'])
                self.logfile.info('request accepted with id: ' + request_id)
                succeeded = waitUntilPositive(partial(AmbariUtils.check_request_completed, self.ambari_server,
                                                      self.cluster_name, request_id))

                result = AmbariUtils.ApiResponse(succeeded, "Check Ambari UI for error details", resp.status, debug_msg)
            else:
                result = AmbariUtils.ApiResponse(False, "{0} {1} {2}".format(resp.status, resp.reason, output),
                                                 resp.status, debug_msg)
        # pylint: disable=W0703
        except Exception as e:
            # log.debug(str(e))
            result = AmbariUtils.ApiResponse(False, str(e), None, debug_msg)

        if result.succeeded:
            return result
        else:
            raise AmbariUtils.ApiException(result)

    def put_stack_version(self, repoconfig, stack_name, stack_version, operating_system, repo_id):
        return self.ambari_api_call(AmbariUtils.HTTP_PUT, self.get_endpoint_stack_repo(stack_name, stack_version,
                                                                                 operating_system, repo_id), repoconfig,
                                    True)

    def post_version_definition(self, vdf_config):
        return self.ambari_api_call(AmbariUtils.HTTP_POST, "version_definitions", vdf_config)

    def post_configuration(self, configuration):
        return self.ambari_api_call(AmbariUtils.HTTP_POST, self.get_endpoint_configurations(), configuration)

    def get_configuration(self, config_type, config_tag, configuration):
        return self.ambari_api_call(AmbariUtils.HTTP_GET,
                                    self.get_endpoint_configurations_for_type_tag(config_type, config_tag),
                                    configuration)

    def post_service(self, service_name):
        return self.ambari_api_call(AmbariUtils.HTTP_POST, self.get_endpoint_services(),
                                    json.dumps({"ServiceInfo": {"service_name": service_name}}))

    def start_service(self, service_name):
        return self.ambari_api_call(AmbariUtils.HTTP_PUT, self.get_endpoint_service(service_name),
                                    AmbariUtils.RESTAPI_START_SERVICE)

    def stop_service(self, service_name):
        return self.ambari_api_call(AmbariUtils.HTTP_PUT, self.get_endpoint_service(service_name),
                                    AmbariUtils.RESTAPI_INSTALL_SERVICE)

    def put_cluster_configuration(self, cluster_config):
        return self.ambari_api_call(AmbariUtils.HTTP_PUT, self.get_endpoint_cluster(), cluster_config, True)

    def add_service(self, http_method, service_name, service_info=RESTAPI_EMPTY_PAYLOAD):
        return self.ambari_api_call(http_method, self.get_endpoint_service(service_name), service_info)

    def post_component_for_service(self, service_name, component_name):
        return self.ambari_api_call(AmbariUtils.HTTP_POST,
                                    self.get_endpoint_service_component(service_name, component_name))

    def post_component_to_host(self, host_name, component_name):
        return self.ambari_api_call(AmbariUtils.HTTP_POST, self.get_endpoint_host(host_name),
                                    json.dumps({"host_components": [{"HostRoles": {"component_name": component_name}}]}))

    def put_all_services_request(self, services_request):
        return self.ambari_api_call(AmbariUtils.HTTP_PUT, self.get_endpoint_services(), services_request)

    def stop_all_installed_services(self):
        return self.put_all_services_request(AmbariUtils.RESTAPI_STOP_ALL_INSTALLED)

    def start_all_services(self):
        return self.put_all_services_request(AmbariUtils.RESTAPI_START_SERVICE)

    def post_cluster_artifact(self, artifact_name, artifact):
        return self.ambari_api_call(AmbariUtils.HTTP_POST, self.get_endpoint_cluster_artifact(artifact_name), artifact)

    def get_service_config_versions(self):
        return self.ambari_api_call(AmbariUtils.HTTP_GET,
                                    self.get_endpoint_service_config_versions()).content

    def get_desired_configs(self):
        return self.ambari_api_call(AmbariUtils.HTTP_GET, self.get_endpoint_desired_configs()).content

    def get_config(self, config_name):
        desired_config_dict = json.loads(self.get_desired_configs())['Clusters']['desired_configs'][config_name]

        return self.ambari_api_call(AmbariUtils.HTTP_GET,
                                    self.get_endpoint_service_config(config_name,
                                                                     desired_config_dict['tag'])).content

    def set_config(self, config_name, config_property, new_content, append=True, sep=" "):
        config = json.loads(self.get_config(config_name))
        # TODO can items list have not one element?
        props = config['items'][0]['properties']
        try:
            old_content = props[config_property]
        # pylint: disable=W0702
        except:
            old_content = props
        desired_config = {"Clusters": {"desired_config": {"type": config_name,
                                                          "tag": "version%s" % int(time.time() * 1000)}}}

        if append:
            new_content = "{0}{1}{2}".format(old_content, sep, new_content)

        props[config_property] = new_content
        desired_config['Clusters']['desired_config']['properties'] = props

        return self.ambari_api_call(AmbariUtils.HTTP_PUT, self.get_endpoint_cluster(), json.dumps(desired_config))

    def enable_kerberos(self, krb_service_config, krb_descriptor, krb_cluster_config, host_list):
        try:
            self.add_service(AmbariUtils.HTTP_POST, AmbariUtils.NAME_SERVICE_KERBEROS)
            self.post_component_for_service(AmbariUtils.NAME_SERVICE_KERBEROS,
                                            AmbariUtils.NAME_COMPONENT_KERBEROS_CLI)
            self.put_cluster_configuration(krb_service_config.replace('\n', '').strip())

            for host in host_list:
                self.post_component_to_host(host, AmbariUtils.NAME_COMPONENT_KERBEROS_CLI)

            self.install_service(AmbariUtils.NAME_SERVICE_KERBEROS)
            self.stop_all_installed_services()
            self.post_cluster_artifact(AmbariUtils.NAME_ARTIFACT_KRB_DESCRIPTOR,
                                       krb_descriptor)
            self.put_cluster_configuration(krb_cluster_config)
            self.start_all_services()

            return AmbariUtils.ApiResponse(True, "Successfully configured service: %s" %
                                           AmbariUtils.NAME_SERVICE_KERBEROS, None)
        # pylint: disable=W0703
        except Exception as e:
            return AmbariUtils.ApiResponse(False, str(e), None)

# ===========================================


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ambari_server=dict(default='localhost', type='str'),
            request_type=dict(required=True, choices=['service',
                                                      'configuration',
                                                      'stack_version',
                                                      'version_definition',
                                                      'component_to_host',
                                                      'component_for_service'], type='str'),
            request_action=dict(required=True, choices=['install',
                                                        'uninstall',
                                                        'start',
                                                        'stop',
                                                        'put',
                                                        'post',
                                                        'get',
                                                        'autoconfigure',
                                                        'config'], type='str'),
            cluster_name=dict(required=False, type='str'),
            service_name=dict(required=False, type='str'),
            component_name=dict(required=False, type='str'),
            encoded_config_map=dict(required=False, type='str'),
            host_name=dict(required=False, type='str'),
            stack_version=dict(required=False, type='str'),
            stack_name=dict(required=False, type='str'),
            operating_system=dict(required=False, type='str'),
            repo_id=dict(required=False, type='str'),
            host_list=dict(required=False, type='list'),
            krb_service_config=dict(required=False, type='str'),
            krb_descriptor=dict(required=False, type='str'),
            krb_cluster_config=dict(required=False, type='str'),
            config_name=dict(required=False, type='str'),
            config_property=dict(required=False, type='str'),
            separator=dict(required=False, type='str'),
            append=dict(default=True, type='bool'),
            config_type=dict(required=False, type='str'),
            config_tag=dict(required=False, type='str'),
            vdf_config=dict(required=False, type='str'),
        )
    )

    ambari = AmbariUtils(module)

    try:
        if module.params['request_type'] == 'service':
            if module.params['request_action'] == 'install':
                response = ambari.install_service(module.params['service_name'])
            elif module.params['request_action'] == 'uninstall':
                response = ambari.uninstall_service(module.params['service_name'])
            elif module.params['request_action'] == 'start':
                response = ambari.start_service(module.params['service_name'])
            elif module.params['request_action'] == 'stop':
                response = ambari.stop_service(module.params['service_name'])
            elif module.params['request_action'] == 'post':
                response = ambari.post_service(module.params['service_name'])
            elif module.params['request_action'] == 'config':
                response = ambari.set_config(module.params['config_name'],
                                             module.params['config_property'],
                                             base64.b64decode(module.params['encoded_config_map']),
                                             sep=module.params['separator'],
                                             append=module.params['append'])
            elif module.params['request_action'] == 'autoconfigure':
                if module.params['service_name'] == AmbariUtils.NAME_SERVICE_KERBEROS:
                    response = ambari.enable_kerberos(module.params['krb_service_config'],
                                                      module.params['krb_descriptor'],
                                                      module.params['krb_cluster_config'],
                                                      module.params['host_list'])
                else:
                    module.fail_json("Auto-configuration not supported for service: %s" % module.params['service_name'])
            else:
                module.fail_json(msg="Unsupported request action: " + ambari.request_action + " for request type: " + ambari.request_type)
        elif module.params['request_type'] == 'configuration':
            if module.params['request_action'] == 'put':
                response = ambari.put_cluster_configuration(base64.b64decode(module.params['encoded_config_map']))
            elif module.params['request_action'] == 'post':
                response = ambari.post_configuration(base64.b64decode(module.params['encoded_config_map']))
            elif module.params['request_action'] == 'get':
                response = ambari.get_configuration(module.params['config_type'],
                                                    module.params['config_tag'],
                                                    base64.b64decode(module.params['encoded_config_map']))
            else:
                module.fail_json(msg="Unsupported request action: " + ambari.request_action + " for request type: " + ambari.request_type)
        elif module.params['request_type'] == 'stack_version':
            if module.params['request_action'] == 'put':
                response = ambari.put_stack_version(base64.b64decode(module.params['encoded_config_map']),
                                                    module.params['stack_name'],
                                                    module.params['stack_version'],
                                                    module.params['operating_system'],
                                                    module.params['repo_id'])
            else:
                module.fail_json(msg="Unsupported request action: " + ambari.request_action + " for request type: " + ambari.request_type)
        elif module.params['request_type'] == 'version_definition':
            if module.params['request_action'] == 'post':
                response = ambari.post_version_definition(base64.b64decode((module.params['vdf_config'])))
            else:
                module.fail_json(msg="Unsupported request action: " + ambari.request_action + " for request type: " + ambari.request_type)
        elif module.params['request_type'] == 'component_to_host':
            if module.params['request_action'] == 'post':
                response = ambari.post_component_to_host(module.params['host_name'], module.params['component_name'])
            else:
                module.fail_json(msg="Unsupported request action: " + ambari.request_action + " for request type: " + ambari.request_type)
        elif module.params['request_type'] == 'component_for_service':
            if module.params['request_action'] == 'post':
                response = ambari.post_component_for_service(module.params['service_name'], module.params['component_name'])
            else:
                module.fail_json(msg="Unsupported request action: " + ambari.request_action + " for request type: " + ambari.request_type)
        else:
            module.fail_json(msg="Unsupported request type:" + ambari.request_type)
    except AmbariUtils.ApiException as api_ex:
        response = api_ex.api_response

    if not response.succeeded:
        module.fail_json(msg=response.msg, debug_msg=response.debug_msg)

    result = {}
    result['changed'] = True
    result['response'] = response.msg

    if response.debug_mode:
        result['debug'] = response.debug_msg

    # pylint: disable=W0142
    module.exit_json(**result)


if __name__ == '__main__':
    main()
