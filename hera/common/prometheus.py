import os
import sys
import json
import logging
import requests
import time
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from requests.packages.urllib3.exceptions import InsecureRequestWarning,InsecurePlatformWarning,SNIMissingWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)

all_memory_data = {}
all_load_data = {}

IM_URL = os.environ.get("SERVER_URL", 'https://im-api.datahub.only.sap')
cluster_name = os.environ.get("K8S_CLUSTER_NAME")
NAMESPACE = os.environ.get("NAMESPACE")
KUBECONFIG = os.environ.get("KUBECONFIG")

RETRY_TIMES = os.environ.get('RETRY_TIMES', 4)
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 60))

color_list= ['red', 'green', 'skyblue', 'blue', 'black', 'orange', 'yellow', 'brown', 'purple', 'gray']

def run_request(function, *args, **kwargs):
    '''
    send IM API call with retry
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

def prometheus_query (query_list, start_time, end_time, step, is_memory=True):
    node_json = {}
    unix_start_time = int(time.mktime(start_time.timetuple()))
    unix_end_time = int(time.mktime(end_time.timetuple()))
    for key, query in query_list.items():
        query_url = "http://localhost:9090/api/v1/query_range?query={}&start={}&end={}&step={}".format(query,unix_start_time,unix_end_time,step)
        
        error_num = 0

        while True:
            try:
                ret = run_request(requests.get, query_url)
                if ret.status_code in [200, 201]:
                    data = ret.json()
                    value_dimen = data['data']['result'][0]['values']
                    value_data = []
                    value_time = []
                    for value_list in value_dimen:
                        # value_list[0] is the sampling time
                        # value_list[1] is the sampling real data (Memory or CPU load)
                        if is_memory:
                            value_list[1]=int(value_list[1])/1024/1024/1024
                        else:
                            value_list[1]=float(value_list[1]) 

                        value_time.append(value_list[0])
                        value_data.append(value_list[1])

                    node_json[key] = [value_time, value_data]
                    break
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

    return node_json

def memory_query(node, start_time, end_time, step=14):
    Apps_query = "node_memory_MemTotal_bytes{node=~\"" + node + "\"} - node_memory_MemFree_bytes{node=~\"" + node + "\"} - node_memory_Buffers_bytes{node=~\"" + node + "\"} - node_memory_Cached_bytes{node=~\"" + node + "\"} - node_memory_SwapCached_bytes{node=~\"" + node + "\"} - node_memory_Slab_bytes{node=~\"" + node + "\"} - node_memory_PageTables_bytes{node=~\"" + node + "\"} - node_memory_VmallocUsed_bytes{node=~\"" + node + "\"}"
 
    Cached_query = "node_memory_Cached_bytes{node=~\"" + node + "\"}"

    query_json = {"Apps": Apps_query, 
                  "Cached": Cached_query}

    all_memory_data[node] = prometheus_query (query_json, start_time, end_time, step, True)

def cpu_load_query(node, start_time, end_time, step=14):
    duration_list = ['1', '5' , '15']
    query_json = {}
    for duration in duration_list:
        duration_query = "sum(node_load" + duration + "{node=~\"" + node + "\"}) / sum(kube_node_status_capacity{resource=\"cpu\",node=~\"" + node + "\"})"

        key = duration + "-min avg"
        query_json[key] = duration_query

    all_load_data[node] = prometheus_query (query_json, start_time, end_time, step, False)

def get_cluster_content(cls_name):
    '''
    get cluster definition from IM
    '''
    header = get_auth_header()
    url = IM_URL + '/api/v1/tasks/deployment?kc_name=' + cls_name
    error_num = 0

    while True:
        try:
            ret = requests.get(url, headers=header, verify=False)
            if ret.status_code == 200:
                data = ret.json()
                if 'tasks' in data and data['tasks'] != '[]':
                    tasks = data['tasks']
                    tasks = tasks.strip().replace('\\n', '').replace(
                        '\\', '').replace('"system/system"', 'system/system')
                    clsr = json.loads(tasks)[0]
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

def get_auth_header():
    """
    Apply for auth header, if failed, apply for max 3 times.
    return: header
    """

    if 'IM_AUTH_HEADER' in os.environ:
        token = os.environ['IM_AUTH_HEADER']
    elif  'IM_TOKEN' in os.environ:
        token = os.environ['IM_TOKEN']  
    else:
        auth_file_tmp=os.popen('find /infrabox/inputs -mindepth 2 -maxdepth 2 -name auth_header.txt')
        auth_file=auth_file_tmp.read().replace('\n','')
        print(auth_file)
        with open(auth_file, 'r') as f:
            lines = f.read()
        token = lines.replace('Authorization: Bearer ', '')
    return {'Authorization': 'Bearer {}'.format(token)}

def is_k8s_available(cluster_name):
    '''
    Check whether k8s cluster is available where the infrabox job will be reran on it
    '''
    clsr_json = get_cluster_content(cluster_name)
    if (clsr_json is None) or (clsr_json == {}):
        return False
    if clsr_json[7].lower() == 'removed':
        return False
    logging.debug('k8s cluster (%s) is available', cluster_name)
    return True

def get_cluster_duration(cluster_name):
    '''
    Get the cluster duration time
    start_time: the creation time of cluster
    end_time: the current time
    '''
    clsrJson = get_cluster_content(cluster_name)
    if clsrJson == {}:
        return False
    start_time = datetime.strptime(clsrJson[3],'%Y-%m-%d %H:%M:%S.%f')
    return start_time, datetime.now()        
    
def get_node():
    '''
    Get the cluster node list
    '''
    try:
        get_node_cmd = "export KUBECONFIG=" + KUBECONFIG + " && kubectl get nodes -o=jsonpath='{.items[*].metadata.name}'"

        r = os.popen(get_node_cmd)
        text = r.read()
        r.close()
        nodes_tmp = text.split(' ')
        nodes_list = list(filter(None, nodes_tmp))

        return nodes_list
    except Exception as err:
        logging.warning("get DI nodes return exception for %s ", str(err))
        return None

def kube_port():
    '''
    kubectl port-forward diagnostics-prometheus-server to localhost:9090
    '''
    kube_port_cmd = 'kubectl port-forward diagnostics-prometheus-server-0 9090 -n ' + NAMESPACE + ' &'
    result = os.system(kube_port_cmd)
    time.sleep(5)
    if result != 0:
        logging.error('kubectl port-forward failed')

def draw_memory_picture(file_name, x1, x2, file_value, ylabel_value=''):
    '''
    The value of all nodes will be drawn in a picture 
    '''
    nodes_num = len(file_value)
    #sub picture setting, locations, and all lines share the same x axis
    fig, ax = plt.subplots(figsize=(12,8),ncols=1,nrows=nodes_num, sharex=True)

    plt.figure(file_name)
    plt.title(file_name)
    # space between sub picture 
    plt.subplots_adjust(wspace =0, hspace = 20)
    plt.gcf().autofmt_xdate()

    sub_picture = 0
    for node_key, node_value in file_value.items():
        # get the max and min value of each line
        value_i = 0
        for key, value_tmp in node_value.items():
            value = value_tmp[1]
            if value_i == 0:
                min_value = min(value)
                max_value = max(value)
            else:
                min_value = min(value) if min(value) < min_value else min_value 
                max_value = max(value) if max(value) > max_value else max_value
            value_i += 1

        draw_min_value = min_value - (max_value - min_value)/10
        draw_max_value = max_value + (max_value - min_value)/10
        ax[sub_picture].set_ylim(draw_min_value, draw_max_value)
        
        color_i = 0
        for key, value in node_value.items():
            # transfer str to datetime
            x = [datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(d)),'%Y-%m-%d %H:%M:%S') for d in value[0]]

            ax[sub_picture].plot(x, value[1], color=color_list[color_i], label=key, linewidth=0.8)

            color_i += 1
        # display label
        ax[sub_picture].legend() 
        sub_title = 'Node: ' + node_key
        ax[sub_picture].set_title(sub_title)
        if sub_picture == (nodes_num - 1) :
            ax[sub_picture].set_xlabel('DI life Cycle (UTC timezone)')
        ax[sub_picture].set_ylabel(ylabel_value)
        sub_picture += 1

    # save the whole picture
    picture_name = file_name + '.png'
    fig.savefig(picture_name)

    #fig.show()

if __name__ == "__main__":

    logging.info('DI diagnostics-prometheus')
    if not is_k8s_available(cluster_name):
        logging.error('K8s cluster %s is not available', cluster_name)
        sys.exit(1)

    start_time, end_time = get_cluster_duration(cluster_name)

    logging.info('Get the cluster nodes')
    nodes_list = get_node()
    if nodes_list is None:
        logging.error('Failed to get the K8s cluster %s nodes', cluster_name)
        exit(1)

    logging.info('kubectl port-forward diagnostics-prometheus-server to localhost:9090')
    kube_port()
 
    logging.info('Get the Memory/CPU value for nodes')
    for node_item in nodes_list:
        memory_query(node_item, start_time, end_time)
        cpu_load_query(node_item, start_time, end_time)

    if not all_memory_data:
        logging.error('Failed to get the k8s cluster %s Memory value', cluster_name)
        exit(1)

    logging.info('Draw the Memory picture, all nodes will be drawn in one picture')
    memory_picture = "Memory" 
    ylabel = 'Memory (G)'        
    draw_memory_picture(memory_picture, start_time, end_time, all_memory_data, ylabel)

    if not all_load_data:
        logging.error('Failed to get the k8s cluster %s CPU Load value', cluster_name)
        exit(1)

    logging.info('Draw the CPU Load picture, all nodes will be drawn in one picture')
    load_pitcure = "CPU_Load"           
    draw_memory_picture(load_pitcure, start_time, end_time, all_load_data)
    sys.exit(0)
