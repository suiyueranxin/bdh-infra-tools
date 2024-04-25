import os
import logging
import requests
import time
import datetime
import json

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


WAIT_INTERACTIVE = int(os.environ.get("CHECK_INTERVAL", 60))
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 60))
RETRY_TIMES = os.environ.get('RETRY_TIMES', 4)
IM_URL = os.environ.get("SERVER_URL", 'https://im-api.datahub.only.sap')
GERRIT_CHANGE_BRANCH = os.environ.get("GERRIT_CHANGE_BRANCH")
PROVISION_PLATFORM = os.environ.get("PROVISION_PLATFORM")
USE_FOR = os.environ.get("USE_FOR", "")
VORA_VERSION = os.environ.get('VORA_VERSION')
K8S_CLUSTER_NAMES = os.environ.get('K8S_CLUSTER_NAMES', '')
EXTEND_DAYS = int(os.environ.get('EXTEND_DAYS', '14'))

def run_request(function, *args, **kwargs):
    '''
    execte requests with retry
    '''
    error_num = 0
    print_ret_content = False
    if kwargs.get('print_ret_content') is not None:
        print_ret_content = kwargs.get('print_ret_content')
        del kwargs['print_ret_content']
    while True:
        try:
            ret = function(*args, verify=False, **kwargs)
        except Exception as err:
            logging.warning("Request got exception for %s ", str(err))
            error_num = error_num + 1
            # retry for RETRY_TIMES
            if error_num < RETRY_TIMES:
                logging.info("Wait for %d seconds and retry", CHECK_INTERVAL)
                time.sleep(CHECK_INTERVAL)
            else:
                logging.error(
                    "Fail to make request for getting exceptions for %d seconds!", RETRY_TIMES)
                raise
        else:
            if print_ret_content:
                logging.debug(
                    'Make request to server, return message is:\n '
                    'status_code:%d,\n content:%s', ret.status_code, ret.content)
            return ret

def get_auth_header():
    """
    Apply for auth header, if failed, apply for max 3 times.
    return: header
    """
    if 'IM_AUTH_HEADER' in os.environ:
        token = os.environ['IM_AUTH_HEADER']
        return {'Authorization': 'Bearer {}'.format(token)}
    else:
        logging.error('please set the IM_AUTH_HEADER in infrabox secret.')
        exit

def get_cluster_content(cls_name):
    '''
    get cluster definition from IM
    '''
    header = get_auth_header()
    url = IM_URL + '/api/v1/tasks/deployment?kc_name=' + cls_name
    error_num = 0

    while True:
        try:
            ret = run_request(requests.get, url, headers=header)
            if ret.status_code == 200:
                tasks_str = json.loads(ret.content)['tasks']
                tasks = json.loads(tasks_str)
                clsr = tasks[0]
                return clsr
            else:
                error_num = error_num + 1
                # retry for RETRY_TIMES
                if error_num < RETRY_TIMES:
                    logging.info("Wait for %d seconds and retry", CHECK_INTERVAL)
                    time.sleep(CHECK_INTERVAL)
                else:
                    logging.error(
                        "Fail to get cluster definition for RETRY_TIMES %d !", RETRY_TIMES)
                    return None
        except Exception as err:
            logging.warning("Request got exception for %s ", str(err))
            return None


def is_k8s_available(cluster_name):
    '''
    Check whether k8s cluster is available
    '''
    clsr_json = get_cluster_content(cluster_name)
    if (clsr_json is None) or (clsr_json == {}) or clsr_json[7].lower() == 'removed':
        logging.debug('k8s cluster (%s) is not available', cluster_name)
        return False
    else:    
        logging.debug('k8s cluster (%s) is available', cluster_name)
        return True

def extendCluserLife(cluster_name, extend_days=EXTEND_DAYS):
    '''
    extend cluster with 'extend_time' day
    '''

    header = get_auth_header()

    clsrJson = get_cluster_content(cluster_name)
    created_time = datetime.datetime.strptime(clsrJson[3].split('.')[0],'%Y-%m-%d %H:%M:%S')
    expired_time = datetime.datetime.strptime(clsrJson[4].split('.')[0],'%Y-%m-%d %H:%M:%S')
    logging.info("The created time of cluster {} is {}!".format(cluster_name, created_time))
    logging.info("The expired time of cluster {} is {}, before extended!".format(cluster_name, expired_time))
    
    if (expired_time - created_time).days >= extend_days:
        logging.info("skip to extend expired time, for the expired time is already >= {} days".format(extend_days))
        return True

    # calculating extend time needs to minus the amount of time that cluster has been alive
    avilable_days = (datetime.datetime.now() - created_time).days
    avilable_hours = (datetime.datetime.now() - created_time).seconds / 3600
    extend_hours = 24*extend_days - (avilable_days*24 + avilable_hours)
    url = IM_URL + '/api/v1/clusters/k8s/%s/expiration/%s' % (cluster_name,str(extend_hours))

    logging.info("extend the cluster {} with {} days!".format(cluster_name, extend_days))
    try:
        ret = run_request(requests.patch, url, headers=header)
        # if ret.status_code = 200, the expired time extended extend_time.
        # if ret.status_code = 500, the expired time is larger than the (current time + extended_time), no need to extend the expire time.
        if ret.status_code == 200 or ret.status_code == 500:
            clsrJson = get_cluster_content(cluster_name)
            expired_time = datetime.datetime.strptime(clsrJson[4].split('.')[0],'%Y-%m-%d %H:%M:%S')
            logging.info("The expired time of cluster {} is {}, after extended!".format(cluster_name, expired_time))
            return True
        else:
            logging.error("extend cluster {} failed with ret.status_code= {} ".format(cluster_name, str(ret.status_code)))
            return False
    except Exception as err:
        logging.warning("Request got exception for %s ", str(err))
        return False

def deletionCluser(cluster_name):
    '''
    delete k8s cluster
    '''

    url = IM_URL + '/api/v1/tasks/' + cluster_name
    try:
        ret = run_request(requests.delete, url, headers=header)
        if ret.status_code != 200 and ret.status_code != 500:
            logging.warning("Request got exception for %s ", str(ret.content))
    except Exception as err:
        logging.warning("Request got exception for %s ", str(err))

def get_should_deleted_cluster(excluded_cluster_list=[], extend_days=EXTEND_DAYS ):
    '''
    get the clustes which should be deleted, the cluster must meet these condition:
    - the cluster is not in the current cluster list
    - the cluster is created in 2*EXTEND_DAYS days
    - the version starts with the current cluster version 'xxxx.yy'
    - the cluster is created in the project 'https://infrabox.datahub.only.sap/dashboard/#/project/milestone-validation'
    - the expired time of cluster is already extended to EXTEND_DAYS days
    - the cluster is still aviable
    - the cluster is not reserved 
    - the descritption can not contain 'reserve'
    '''

    should_delete_clusters_list = []
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    daysago = 2*extend_days
    start_time = (datetime.datetime.now() - datetime.timedelta(days = daysago)).strftime("%Y-%m-%d %H:%M:%S")

    customer_name = USE_FOR + ' '
    version_prefix = VORA_VERSION.rsplit('.', 1)[0]
    url = IM_URL + '/api/v1/tasks/deployment/range/%s/%s?kc_plat=%s&kc_customize_name=%s&kc_bdh_ver=%s' % (start_time, end_time, PROVISION_PLATFORM, customer_name, version_prefix)

    try:
        ret = run_request(requests.get, url, headers=header)
        if ret.status_code != 200:
            logging.warning("Request got exception for %s ", str(ret.content))

        cluster_tasks_str = json.loads(ret.content)['tasks']
        cluster_tasks = json.loads(cluster_tasks_str)
        logging.info("tasks of clusters which should be deleted are %s", cluster_tasks)
        for task in cluster_tasks:
            created_time = datetime.datetime.strptime(task[3].split('.')[0],'%Y-%m-%d %H:%M:%S')
            expired_time = datetime.datetime.strptime(task[4].split('.')[0],'%Y-%m-%d %H:%M:%S')
            cluster_description = cluster_tasks[0][6]['environment']['DESCRIPTION'].lower()
            if task[0] not in excluded_cluster_list \
            and (expired_time - created_time).days == extend_days \
            and cluster_description.find('reserve') == -1 \
            and task[7].lower() != 'reserved' \
            and task[7].lower() != 'removed':
                should_delete_clusters_list.append(task[0])

    except Exception as err:
        logging.warning("Request got exception for %s ", str(err))

    finally:
        logging.info("the clusters should be deleted are  " + " ".join(should_delete_clusters_list))
        return should_delete_clusters_list

if __name__ == '__main__':
    header = get_auth_header()
    current_cluster_list = []

    # Only reserve cluster for release branch
    if not GERRIT_CHANGE_BRANCH.startswith('rel-') and USE_FOR != 'MILESTONE_VALIDATION':
        logging.info('if the branch does not start with rel- or use_for is not MILESTONE_VALIDATION, skip this job')
        exit()

    if int(EXTEND_DAYS) > 14:
        EXTEND_DAYS = 14
    elif int(EXTEND_DAYS) < 2:
        EXTEND_DAYS = 2

    if K8S_CLUSTER_NAMES:
        logging.info('K8S_CLUSTER_NAMES = {}'.format(K8S_CLUSTER_NAMES))
        if PROVISION_PLATFORM == 'GKE':
            # For GKE, there is 4 clusters at one milestone-validation, reserve all available clusters.
            k8s_cluster_name_list = K8S_CLUSTER_NAMES.split(',')
            for cluster_item in k8s_cluster_name_list:
                cluster = cluster_item.split(':')[1]
                if is_k8s_available(cluster):
                    current_cluster_list.append(cluster)
        else:
            # For other platforms, check if the current cluster is still available, and reserve it.
            cluster = K8S_CLUSTER_NAMES.split(':')[1]
            if is_k8s_available(cluster):
                current_cluster_list.append(cluster)
        
        if not current_cluster_list:
            logging.error("No cluster is not available, skip this job")
            exit()

        for cluster in current_cluster_list:
            if not extendCluserLife(cluster, EXTEND_DAYS):
                logging.error("Failed to extend cluster {}".format(cluster))
                exit()
    
        # delete all previous clusters, to keep only 1 cluster is reserved for 1 release branch 1 platform.
        should_delete_clusters_list =  get_should_deleted_cluster(current_cluster_list, EXTEND_DAYS)               
        if should_delete_clusters_list:
            for delete_cluster in should_delete_clusters_list:
                logging.info("delete previous cluster {}".format(delete_cluster))
                deletionCluser(delete_cluster)
    else:
        logging.error("Failed to get the current cluster {}".format(K8S_CLUSTER_NAMES))
        exit()
