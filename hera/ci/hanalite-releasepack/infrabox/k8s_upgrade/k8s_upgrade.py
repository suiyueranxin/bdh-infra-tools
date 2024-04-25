#!/usr/bin/env python

import os
import os.path
import json
import time
import logging
import requests
from kubernetes import client, config
import yaml


class K8sManager(object):
    def __init__(self, kubeconfig_json):
        self.kubeconfig_json = kubeconfig_json
        self.client = self._get_client()
        self.v1 = self.client.CoreV1Api()

    def _get_client(self):
        try:
            loader = config.kube_config.KubeConfigLoader(self.kubeconfig_json)
            client_config = type.__call__(client.Configuration)
            loader.load_and_set(client_config)
            client.Configuration.set_default(client_config)
            return client

        except Exception as e:
            logger.error('Get k8s client failed:%s'% e)
            raise


    def get_pod_status(self, namespace):
        try:
            pod_list = self.v1.list_namespaced_pod(namespace)
            result = {}
            for pod in pod_list.items:
                name = str(pod.metadata.name)
                random_name = name.split("-")[-1]
                name = name[:len(name)-len(random_name)-1]
                name = special_parse(name)
                result[name] = pod.status.phase
            return result
        except Exception as e:
            logger.error('Fail to get k8s pod list: %s'% e)
            raise


def special_parse(name):
    if "vflow" in name:
        name = name[:-5]

    return name

def run_request(function, *args, **kwargs):
    """
    call restAPI for max $max_error_num times trials
    """

    error_num = 0
    while True:
        try:
            ret = function(*args, verify=False, **kwargs)
        except Exception as e:
            logger.warning( "Request got exception for %s " % str(e))
            error_num = error_num + 1
            # retry for max_error_retry_num
            if error_num < max_error_retry_num:
                logger.info("Wait for %d seconds and retry" % check_interval)
                time.sleep(check_interval)
            else:
                logger.error("Fail to make request for getting exceptions for %d seconds!" % max_error_retry_num)
                raise
        else:
            logger.info("Make request to server, return message is:\n status_code:%d,\n content:%s" % (ret.status_code, ret.content) )
            return ret


def get_base_url():

    base_url = "https://im-api.datahub.only.sap"
    return base_url


def get_env(base_url, header):

    env = {
        "environment": {}
    }
    #Currently for DI 3.2 we didn't support k8s 1.26+, so we will use the 1.25 instead. This code is only working in milestone_validation_upgrade job. 
    k8s_version_upgrade_to_temp = str(os.environ.get("K8S_VERSION_UPGRADE_TO", "1.25"))
    vora_target_version = str(os.environ.get("VORA_VERSION", "null"))
    use_for = str(os.environ.get("USE_FOR", ""))
    if vora_target_version.startswith("3.2.") and use_for == "MILESTONE_VALIDATION_upgrade":
        k8s_version_upgrade_to_temp = "1.25"
    print("Target k8s version is" + k8s_version_upgrade_to_temp)

    env["environment"]["K8S_VERSION_UPGRADE_TO"] = k8s_version_upgrade_to_temp
    env["environment"]["PROVISION_PLATFORM"] = str(os.environ.get("PROVISION_PLATFORM", "AWS-EKS"))
    env["environment"]["UPGRADE_TYPE"] = str(os.environ.get("UPGRADE_TYPE", "k8s"))

    
    if env["environment"]["PROVISION_PLATFORM"] == "GKE":
        k8s_version_upgrade_to = get_gke_upgrade_version(base_url, header, k8s_version_upgrade_to_temp)
        if k8s_version_upgrade_to != "":
            env["environment"]["K8S_VERSION_UPGRADE_TO"] = k8s_version_upgrade_to

    if env["environment"]["PROVISION_PLATFORM"] == "AZURE-AKS":
        k8s_version_upgrade_to = get_aks_upgrade_version(base_url, header, k8s_version_upgrade_to_temp)
        if k8s_version_upgrade_to != "":
            env["environment"]["K8S_VERSION_UPGRADE_TO"] = k8s_version_upgrade_to

    return env


def check_env_ready(base_url, cluster_name, header):

    # check for environment is Ready
    max_wait_ready_time = int(os.environ.get("MAX_READY_WAIT", 10800))

    url = '%s/api/v1/clusters/k8s/monitor/status/%s' % (base_url, cluster_name)
    start_time = time.time()
    while time.time() - start_time < max_wait_ready_time:
        ret = run_request(requests.get, url, headers=header)
        if ret.status_code == 200:
            data = ret.json()
            cluster_status = data['monitor_status']
            if cluster_status.upper() == 'RUNNING':
                logger.info("K8s Upgrade is Ready!")
                return True
            elif cluster_status.upper() in ['UPGRADING']:
                logger.warning("K8s Upgrade status is Upgrading!")
            else:
                logger.error("K8s Upgrade status is %s ! Stop waiting when met this type of status!" % cluster_status)
                return False
        else:
            logger.warning("Got unexpected status_code from server, status_code is %d, error information is %s" % (ret.status_code, ret.content))

        logger.warning("K8s Upgrade is NOT Ready yet, wait another %d seconds!" % check_interval)
        time.sleep(check_interval)

    logger.error("K8s Upgrade timeout after %d seconds!" % max_wait_ready_time)
    return False


def start_k8s_upgrade(base_url, cluster_name, header):

    rest_api_path = "/api/v1/tasks/upgrade/k8s/" + cluster_name
    url = base_url + rest_api_path
    env = get_env(base_url, header)
    upgrade_to=env["environment"]["K8S_VERSION_UPGRADE_TO"]
    print("Now upgrade to %s"%upgrade_to)
    ret = run_request(requests.post, url, json=env, headers=header)
    if ret.status_code == 200:
        data = ret.json()
        if data["status"] == "200":
            return True

    return False


def get_auth_header(base_url, owner):
    if 'IM_AUTH_HEADER' in os.environ:
        token = os.environ.get('IM_AUTH_HEADER', '')
        return {'Authorization': 'Bearer {}'.format(token)}
    else:
        sys_account = os.environ.get('SYS_ACCOUNT', '')
        sys_password = os.environ.get('SYS_PASSWORD', '')
        if sys_account is '' or sys_password is '':
            raise RuntimeError("Fail to generate auth header, no SYS_ACCOUNT or SYS_PASSWORD!")

        response = run_request(requests.post, base_url + '/api/v1/users/user/' + owner, data=json.dumps({"username": sys_account, "password": sys_password}))
        # try both /api/v1/users/user/ and /api/v1/user/ for backward capability
        if response.status_code != 200:
            response = run_request(requests.post, base_url + '/api/v1/user/' + owner, data=json.dumps({"username": sys_account, "password": sys_password}))
        if response.status_code != 200: # pylint: disable=no-else-raise
            logger.error("Can not get auth token, API server respond error!")
            raise RuntimeError("Fail to genreate auth header!")
        else:
            token = response.json().get('token')
            return {'Authorization': 'Bearer {}'.format(token)}

def check_pods_ready(pre_pods_status, namespace, k8s_manager):

    # workaroud for SAP Note 2908055
    provision_platform =  os.environ.get("PROVISION_PLATFORM", "AWS-EKS")
    base_bdh_version = os.environ.get("BASE_BDH_VERSION", "2.7.147")
    logger.info("base_bdh_version is %s" % base_bdh_version)
    config_file = str(os.environ.get("KUBECONFIG", ''))
    if provision_platform == "AWS-EKS" and (base_bdh_version.startswith('2.7.') or base_bdh_version.startswith('3.0.') or base_bdh_version.startswith('3.1.')):
        try:
            path_cmd='export KUBECONFIG=' + config_file + ' && kubectl -n ' + namespace + r' patch sts vsystem-vrep --type strategic --patch "{\"spec\": {\"template\": {\"spec\": {\"nodeSelector\": null }}"}}'
            logger.info("workaroud for SAP Note 2908055, need to run this command for AWS-EKS, when lower version is 2.7.* or 3.0.*: %s" % path_cmd)
            os.system(path_cmd)

            vrep_cmd='export KUBECONFIG=' + config_file + ' && kubectl get pods -n ' + namespace + ' |grep vsystem-vrep'
            vrep_result=os.popen(vrep_cmd)
            tmp_vrep_result=vrep_result.read().splitlines()
            if len(tmp_vrep_result) > 0:
                for line in tmp_vrep_result:
                    vrep = line.split()[0]
                    delete_cmd='export KUBECONFIG=' + config_file + ' && kubectl delete pod ' + vrep + ' -n ' + namespace
                    os.system(delete_cmd)
        except Exception as e:
            logger.error('workaround for AWS-EKS failed : %s' % e)
            return False

    # check for environment is Ready
    max_wait_ready_time = int(os.environ.get("MAX_READY_WAIT", 3600))

    start_time = time.time()
    while time.time() - start_time < max_wait_ready_time:
        pods_status = k8s_manager.get_pod_status(namespace)
        logger.info("pods_status:\n" + str(pods_status))
        for name in pre_pods_status:
            if name in pods_status and pre_pods_status[name] == pods_status[name]: # pylint: disable=no-else-continue
                pods_status.pop(name)
                continue
            elif pre_pods_status[name] == "Succeeded" or pre_pods_status[name] == "Failed":
                continue
            else:
                break
        if not pods_status:
            return True
        logger.warning("K8s Upgrade is NOT Ready yet, wait another %d seconds!" % check_interval)
        time.sleep(check_interval)

    logger.error("Check pods timeout after %d seconds!" % max_wait_ready_time)
    return False


def get_namespace(base_url, owner, cluster_name, header):

    namespace = ""

    url = '%s/api/v1/clusters/bdh/%s?page=1&&per_page=10&bdh_name=%s' % (base_url, owner, cluster_name)

    ret = run_request(requests.get, url, headers=header)
    if ret.status_code == 200:
        data = ret.json()
        clusters = data['clusters']
        if len(clusters) != 0:
            clusters = json.loads(clusters)
            if len(clusters) != 0:
                namespace = clusters[0]['kc_namespace']
    return namespace

def upgrade_k8s_by_im():

    cluster_name = os.environ.get("K8S_CLUSTER_NAME", '')
    base_url = get_base_url()

    owner = "SDHINFRA"
    header = get_auth_header(base_url, owner)

    namespace = get_namespace(base_url, owner, cluster_name, header)
    config_file = str(os.environ.get("KUBECONFIG", ''))
    with open(config_file) as f:
        config_json = yaml.safe_load(f)
    k8s_manager = K8sManager(config_json)
    pre_pods_status = k8s_manager.get_pod_status(namespace)
    logger.info("pre_pods_status:\n" + str(pre_pods_status))

    if not pre_pods_status:
        logger.error("Get pre pods status fail!")
        return False

    if not start_k8s_upgrade(base_url, cluster_name, header):
        logger.error("Start k8s upgrade fail!")
        return False

    if not check_env_ready(base_url, cluster_name, header):
        logger.error("K8s upgrade fail!")
        return False

    if not check_pods_ready(pre_pods_status, namespace, k8s_manager):
        logger.error("Check pods status fail!")
        return False

    return True

def get_gke_upgrade_version(base_url, header, gke_short_version):
    gke_version = ""
    url = '%s/api/v1/configs/versions/k8s/GCP-GKE/sap-p-and-i-big-data-vora/europe-west1-b' % (base_url)
    ret = run_request(requests.get, url, headers=header)
    if ret.status_code == 200:
        data = ret.json()
        version_list = data["versions"]
        if len(version_list) > 0:
            for version in version_list:
                if version.startswith(gke_short_version):
                    gke_version = version
    return gke_version

def get_aks_upgrade_version(base_url, header, aks_short_version):
    aks_version = ""
    url = '%s/api/v1/configs/versions/k8s/AZURE-AKS/sap-pi-big-data-validation/westeurope' % (base_url)
    ret = run_request(requests.get, url, headers=header)
    if ret.status_code == 200:
        data = ret.json()
        version_list = data["versions"]
        if len(version_list) > 0:
            for version in version_list:
                if version.startswith(aks_short_version):
                    aks_version = version
    return aks_version

if __name__ == "__main__":

    check_interval = int(os.environ.get("CHECK_INTERVAL", 120))
    max_error_retry_num = int(os.environ.get("MAX_ERROR_RETRY_NUM", 3))

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

    result = upgrade_k8s_by_im()

    if result:
        exit(0)
    else:
        exit(1)
