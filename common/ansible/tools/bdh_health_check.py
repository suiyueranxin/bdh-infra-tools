import os
import sys
import requests
import time
import logging
import threading
import urllib3
urllib3.disable_warnings()
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from junit_xml import TestSuite, TestCase


def requests_retry_session(
        retries=5,
        back_off_factor=0.3,
        status_force_list=range(500, 600),
        session=None):

    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=back_off_factor,
        status_forcelist=status_force_list,
        redirect=5,
    )
    request_retry = HTTPAdapter(max_retries=retry)
    session.mount('http://', request_retry)
    session.mount('https://', request_retry)
    return session


class ServiceCheck(object):
    def __init__(self, bdh_entrypoint_url, login_timeout):
        self.__bdh_entrypoint_url = bdh_entrypoint_url
        self.__login_timeout = login_timeout
        self.__result_list = {}

    def get_result_list(self):
        return self.__result_list

    def __username_login(self, username, password):
        proxies = {"http": None, "https": None, }
        auth = requests.auth.HTTPBasicAuth(username, password)
        url = self.__bdh_entrypoint_url + "/auth/login"
        except_retry = 0
        while except_retry < check_times:
            try:
                resp = requests_retry_session().get(url, auth=auth, verify=False, proxies=proxies, timeout=self.__login_timeout)
                code = resp.status_code
                if code != 200:
                    print(resp.content)
                session_id = resp.cookies['vsystem-session-id']
                break
            except Exception as e:
                code = 0
                session_id = ""
                print(e)
                except_retry += 1
                time.sleep(sleep_time)
        return code, session_id
        
    def __check_single_component(self, session_id, endpoint):
        full_url = self.__bdh_entrypoint_url + endpoint
        cookies = {'vsystem-session-id':session_id}
        except_retry = 0
        while except_retry < check_times:
            try:
                resp = requests_retry_session().get(full_url, cookies=cookies, verify=False, timeout=self.__login_timeout)
                code = resp.status_code
                if code != 200:
                    print(resp.content)
                if code == 401:
                    raise Exception(resp.content)
                break
            except Exception as e:
                code = 0
                print(e)
                except_retry += 1
                time.sleep(sleep_time)
        return code

    def __check_components(self, session_id, connections, user_name, password):
        result_dict = {}
        threads = []
        def target(key, value):
            result_dict[key] = 502
            try:
                result_dict[key] = self.__check_single_component(session_id,value)
            except Exception as e:
                # Check and refresh cookie when check single component failure.
                result_dict[key] = refresh_cookie_and_retry(value)
            if result_dict[key] == 200:
                self.__result_list[key] = "WORKING"
                logger.info("check {} successful".format(key))
            else:
                self.__result_list[key] = "NOT_WORKING"
                logger.warning("check {} failed".format(key))
            
        def refresh_cookie_and_retry(value):
            logger.info("Try to get new session id.")
            # Try to get new valid cookie by BasicAuth login.
            login_return_code, session_id = self.__username_login(user_name,password)
            # Retry to check single component
            try:
                result_dict[key] = self.__check_single_component(session_id, value)
            # If still failed after getting new valid cookie, set the check result as 502.
            except Exception as e:
                result_dict[key] = 502
                print(e)
                return result_dict[key]
            return result_dict[key]

        for key, value in connections.items():
            thread = threading.Thread(target = target, args = [key, value])
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return result_dict

    def __check_connections(self, connections, session_id, user_name, password):
        result_dict = self.__check_components(session_id, connections, user_name, password)

        flag = 0
        for key, value in result_dict.items(): # pylint: disable=unused-variable
            if value == 200:
                flag += 1
        if flag == len(connections):
            return True

        return False

    def check_bdh(self, user_name, password, connections):
        if not connections:
            return True
        login_return_code, session_id = self.__username_login(user_name, password)
        if login_return_code == 200:
            logger.info("username login successful")
            self.__result_list["USER_LOGIN"] = "WORKING"
            logger.info("check USER_LOGIN successful")
            result = self.__check_connections(connections, session_id, user_name, password)
            return result
        elif login_return_code == 401:
            result = False
            logger.error("Invalid password of {}".format(user_name))
            self.__result_list["USER_LOGIN"] = "NOT_WORKING"
            logger.info("check USER_LOGIN failed")
        elif login_return_code == 404:
            result = False
            logger.error("404 not found")
            self.__result_list["USER_LOGIN"] = "NOT_WORKING"
            logger.info("check USER_LOGIN failed")
        elif login_return_code == 0:
            result = False
            logger.error("Get /auth/login Exception")
            self.__result_list["USER_LOGIN"] = "NOT_WORKING"
            logger.info("check USER_LOGIN failed")
        else:
            result = False
            logger.warning("Username login failed: " + str(login_return_code))
        return result

def check_clusters():
    if "SKIP_CLUSTER_CHECK" in os.environ:
        logger.warning("Skip cluster check")
        return True
    if "KUBECONFIG" not in os.environ:
        logger.warning("No kubernetes configuration found, will skip check cluster")
        return False 
    from kubernetes import client, config
    check_result = True
    pod_name = ''
    try:
        config.load_kube_config(os.environ["KUBECONFIG"])
        v1 = client.CoreV1Api()
        result = v1.list_namespaced_pod('kube-system')
        if len(result.items) == 0:
            logger.warning("No resources found") 
            check_result = False
        else:
            for pod in result.items:
                pod_status = str(pod.status.phase)
                pod_name = str(pod.metadata.name)
                if pod_status.upper() != "RUNNING":
                    logger.warning("pod " + pod_name + " is not in running status. Current status: " + pod_status) 
    except Exception as e:
        logger.warning(e)
        check_result = False
    finally:
        case = TestCase('K8S_CLUSTER', 'cluster_check')
        if not check_result:
            failure_info = "k8s cluster status check failed."
            if pod_name and pod_name !='':
                failure_info = failure_info + "Detail: k8s cluster status pod " + pod_name + " is not in running status"
            case.add_failure_info(failure_info)
        suite = TestSuite('K8S_cluster_check', [case])
        with open('/infrabox/upload/testresult/cluster_check_result.xml', 'w') as f:
            TestSuite.to_file(f, [suite])
    return check_result

def check_environments():
    if os.getenv("VORA_TENANT", "") != "" \
            and os.getenv("VORA_USERNAME", "") != "" \
            and os.getenv("VORA_PASSWORD", "") != "" \
            and os.getenv("VORA_SYSTEM_TENANT_PASSWORD", "") != "" \
            and os.getenv("VSYSTEM_ENDPOINT", "") != "":
        return True
    return False


def get_connections(input_keys, connection_dict):

    connections = {}
    input_keys = input_keys.strip().split(",")

    for input_key in input_keys:
        for key in connection_dict:
            if input_key.strip() == key:
                connections[key] = connection_dict[key]

    return connections


def write_to_file(check_list, symbol):
    with open('/infrabox/output/env.sh', 'a+') as f:
        for key, value in check_list.items():
            f.write("export " + symbol + key + "=" + value + "\n")


def get_logger():
    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(lineno)d - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def write_to_xml_report(default_result_list, system_result_list):

    default_cases = []
    system_cases = []

    for key, value in default_result_list.items():
        case = TestCase(key, "default_tenant")
        if value != "WORKING":
            case.add_failure_info(key + "is not working!")
        default_cases.append(case)

    for key, value in system_result_list.items():
        case = TestCase(key, "system_tenant")
        if value != "WORKING":
            case.add_failure_info(key + " is not working!")
        system_cases.append(case)

    default_suite = TestSuite("BDH_health_check_default_tenant", default_cases)
    system_suite = TestSuite("BDH_health_check_system_tenant", system_cases)

    with open('/infrabox/upload/testresult/health_check_result.xml', 'w') as f:
        TestSuite.to_file(f, [default_suite, system_suite])

if __name__ == "__main__":

    logger = get_logger()

    check_times = int(os.getenv("HEALTH_CHECK_CHECK_TIMES", 3))
    login_timeout = int(os.getenv("HEALTH_CHECK_LOGIN_TIMEOUT", 120))
    sleep_time = int(os.getenv("HEALTH_CHECK_SLEEP_TIME", 60))

    logger.info("HEALTH_CHECK_CHECK_TIMES = {}".format(check_times))
    logger.info("HEALTH_CHECK_LOGIN_TIMEOUT = {}".format(login_timeout))
    logger.info("HEALTH_CHECK_SLEEP_TIME = {}".format(sleep_time))

    if 'DIS_VERSION' in os.environ:
        logger.info('## skip check_bdh for DI:E')
        exit(0)
 
    if check_environments() is False:
        logger.error("Get environments failed!")
        sys.exit(1)
    check_clusters()
    default_dict = {
        "LAUNCHPAD": "/app/datahub-app-launchpad/",
        "CONNECTION_MANAGEMENT": "/app/datahub-app-connection/",
        "METADATA_EXPLORER": "/app/datahub-app-metadata/#metadata/",
        "PIPELINE_MODELER": "/app/modeler-ui/",
        "PIPELINE_MODELER_INSTANCE": "/app/pipeline-modeler/service/healthcheck",
        "MONITORING": "/app/datahub-app-logging/health",
        "CUSTOMER_DATA_EXPORT": "/app/datahub-app-dex/#/exports/",
        "FLOWAGENT": "/app/data-hub-flow-agent/"
    }

    system_dict = {
        "LAUNCHPAD": "/app/datahub-app-launchpad/",
        "SYSTEM_MANAGEMENT": "/app/datahub-app-system-management/"
    }

    default_list = '''LAUNCHPAD, CONNECTION_MANAGEMENT, METADATA_EXPLORER, PIPELINE_MODELER,
                    PIPELINE_MODELER_INSTANCE, LICENSE_MANAGER, MONITORING,
                    CUSTOMER_DATA_EXPORT, FLOWAGENT'''

    system_list = 'LAUNCHPAD, SYSTEM_MANAGEMENT, GRAFANA, KIBANA, LICENSE_MANAGER'
    
    # determine check list
    default_list = os.getenv('BDH_HEALTH_CHECK_DEFAULT', default_list)
    system_list = os.getenv('BDH_HEALTH_CHECK_SYSTEM', system_list)

    # if the profile is not di-platform-full, remove the VORA_TOOLS from health check	
    base_profile = os.environ.get("BASE_PROFILE", "")	
    vora_version = os.environ.get("VORA_VERSION", "")
    branch = os.environ.get("GERRIT_CHANGE_BRANCH", "")
    base_bdh_version = os.environ.get("BASE_BDH_VERSION", "")
    #only rel-3.x, and release branches before and include rel-2108	support vora	

    if base_profile == "di-platform-full":
        # DM01-2974 keep AUDIT_LOG_VIEWER for on-premise only
        default_dict["AUDIT_LOG_VIEWER"] = "/app/datahub-app-auditlog/"
        default_list += ", AUDIT_LOG_VIEWER"
        default_dict["VORA_TOOLS"] = "/app/vora-tools/"
        system_dict["VORA_TOOLS"] = "/app/vora-tools/"
        default_dict["LICENSE_MANAGER"] = "/app/license-manager/"
        system_dict["LICENSE_MANAGER"] = "/app/license-manager/"
        default_list += ", VORA_TOOLS"
        system_list += ", VORA_TOOLS"
        default_list += ", LICENSE_MANAGER"
        system_list += ", LICENSE_MANAGER"
    if branch == "rel-3.3":
        default_dict["LICENSE_MANAGER"] = "/app/license-manager/"
        system_dict["LICENSE_MANAGER"] = "/app/license-manager/"
        default_list += ", LICENSE_MANAGER"
        system_list += ", LICENSE_MANAGER"

    # For on_premise:
    # the api '/app/pipeline-modeler/' can work well in rel-3.1 and rel-3.2
    # the api '/app/modeler-ui/' can only work well in rel-3.2
    # 'base_bdh_version' is for upgrade test only, for 3.2 upgrade from 3.1 use '/app/pipeline-modeler/'.
    # For 3.2 fresh install, use '/app/modeler-ui/'
    version_tmp = base_bdh_version if base_bdh_version else vora_version
    if version_tmp and version_tmp.startswith('3.1') and "PIPELINE_MODELER" in default_dict:
        default_dict["PIPELINE_MODELER"] = "/app/pipeline-modeler/"

    # create login info
    default_connections = get_connections(default_list, default_dict)
    system_connections = get_connections(system_list, system_dict)

    default_user = os.getenv("VORA_TENANT", "") + "\\" + os.getenv("VORA_USERNAME", "")
    default_password = os.getenv("VORA_PASSWORD", "")

    system_user = "system" + "\\" + "system"
    system_password = os.getenv("VORA_SYSTEM_TENANT_PASSWORD", "")

    vsystem_endpoint = os.getenv("VSYSTEM_ENDPOINT", "")

    default_check = ServiceCheck(vsystem_endpoint, login_timeout)
    system_check = ServiceCheck(vsystem_endpoint, login_timeout)

    # do health check
    if not (default_connections or system_connections):
        logger.info('## skip check_bdh')
        exit(0)
    else:
        result = default_check.check_bdh(default_user, default_password, default_connections) and \
                 system_check.check_bdh(system_user, system_password, system_connections)

    logger.info("default result list: \n{}".format(default_check.get_result_list()))
    logger.info("system result list: \n{}".format(system_check.get_result_list()))

    write_to_file(default_check.get_result_list(), "DEFAULT_")
    write_to_file(system_check.get_result_list(), "SYSTEM_")

    logger.info('write to xml report')
    write_to_xml_report(default_check.get_result_list(), system_check.get_result_list())

    if result:
        logger.info('## check_bdh successful')
        exit(0)
    else:
        logger.info('## check_bdh unsuccessful')
        exit(1)
