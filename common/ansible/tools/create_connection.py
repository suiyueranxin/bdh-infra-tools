import requests
import os, sys
import json
import time
import logging
from requests.auth import HTTPBasicAuth

check_interval = int(os.environ.get("CHECK_INTERVAL", 60))
max_error_retry_num = int(os.environ.get("MAX_ERROR_RETRY_NUM", 3))

# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create file handler and set level to debug
log_file_path='/infrabox/output/create_data_connection.log'
fh = logging.FileHandler(log_file_path, mode='w')
fh.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(lineno)d - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)


def runRequest(function, *args, **kwargs):
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
                logger.info( "Wait for %d seconds and retry" % check_interval)
                time.sleep(check_interval)
            else:
                logger.error( "Fail to make request for getting exceptions for %d seconds!" % max_error_retry_num)
                raise
        else:
            return ret

def create_connection(con_config):
    request_json = {
        'id': con_config['connection_id'],
        'description': con_config['description'],
        'licenseRelevant': True,
        'type': con_config['connection_type'],
        'contentData': con_config['content_data'],
        'changedNote': '',
        'tags': []
    }
    url = con_config['vsystem_endpoint'] + '/app/datahub-app-connection/connections'
    username = con_config['default_tenant'] + "\\" + con_config['default_username']
    header = { 'X-Requested-With': 'Fetch' }
    ret = runRequest(requests.post, url=url, auth=HTTPBasicAuth(username, con_config['default_password']), json=request_json, headers=header)
    if ret.status_code not in [200, 201]:
        if ret.status_code == 400 and len(ret.content):
            try:
                response_json = ret.json()
                if response_json['code'] == "10015" and "already existed" in response_json['message'].lower():
                    return True
            except Exception:
                pass
        if ret.status_code == 409 and len(ret.content):
            try:
                response_json = ret.json()
                if response_json['code'] == "10015" and "already exists" in response_json['message'].lower():
                    return True
            except Exception:
                pass
        logger.error("create connection failed! code: %d", ret.status_code)
        logger.error(ret.content)
        return False
    else:
        return True

def check_if_connection_is_ready(con_config):
    url = con_config['vsystem_endpoint'] + '/app/datahub-app-connection/connections/%s/status' % con_config['connection_id']
    username = con_config['default_tenant'] + "\\" + con_config['default_username']
    ret = runRequest(requests.get, url=url, auth=HTTPBasicAuth(username, con_config['default_password']))
    check_result = False
    if ret.status_code == 200:
        data = ret.json()
        if 'status' in data and data['status'] == 'OK':
            check_result = True
    return check_result

def create_and_check_connection_with_retry(con_config):
    current_time = 0
    max_retry_time = 10
    last_ret = False
    while current_time < max_retry_time:
        last_ret = create_connection(con_config)
        if last_ret:
            current_time = 0
            last_ret = False
            break
        else:
            logger.error('create connection %s failed, retry!' % con_config['connection_id'])
            current_time += 1
            time.sleep(30)
            continue

    while current_time < max_retry_time:
        time.sleep(30)
        last_ret = check_if_connection_is_ready(con_config)
        if last_ret:
            break 
        else:
            logger.error('check connection %s is not ready, retry!' % con_config['connection_id'])
            current_time += 1
    if not last_ret:
        logger.error('error when creating connection %s, exit!' % con_config['connection_id'])
    return last_ret

def get_content_data_gcs(im_base_url, im_headers):
    url = im_base_url + '/api/v1/data/connection/GCP/GCS/sap-p-and-i-big-data-vora'
    ret = runRequest(requests.get, url=url, headers=im_headers)
    if ret.status_code != 200:
        logger.error("Failed to get gcs data source information!")
        return None
    else:
        data = ret.json()
        user_key_file = json.dumps(data['connection']['user_key_file'])
        content_data = {
            'type': 'GCS',
            'gcsProjectId': 'sap-p-and-i-big-data-vora',
            'gcsKeyFile': user_key_file,
            'rootPath': '/data-hub-im/DI_DATA_LAKE'
        }
        return content_data

def get_content_data_s3(im_base_url, im_headers):
    url = im_base_url + '/api/v1/data/connection/AWS/S3/common-login'
    ret = runRequest(requests.get, url=url, headers=im_headers)
    if ret.status_code != 200:
        logger.error("Failed to get s3 data source information!")
        return None
    else:
        data = ret.json()
        custom_endpoint = data['connection']['custom_endpoint']
        s3_access_key = data['connection']['aws_access_key']
        s3_secret_key = data['connection']['aws_secret_key']
        content_data = {
            'type': 'S3',
            's3Endpoint': custom_endpoint,
            's3AccessKey': s3_access_key,
            's3SecretKey': s3_secret_key,
            'rootPath': '/data-hub-im/DI_DATA_LAKE'
        }
        return content_data

def get_content_data_hdfs(im_base_url, im_headers):
    url = im_base_url + '/api/v1/data/connection/AWS/HDFS/im-hadoop-aws'
    ret = runRequest(requests.get, url=url, headers=im_headers)
    if ret.status_code != 200:
        logger.error("Failed to get s3 data source information!")
        return None
    else:
        data = ret.json()
        hdfs_endpoint = data['connection']['HDFS_IP']
        hdfs_port = int(data['connection']['HDFS_webhdfs_port'])
        content_data = {
            'host': hdfs_endpoint,
            'port': hdfs_port,
            'protocol': 'webhdfs',
            'user': 'hdfs'
        }
        return content_data

# use this function later
def get_content_data_oss(im_base_url, im_headers):
    url = im_base_url + '/api/v1/data/connection/AliCloud/OSS/oss-im'
    ret = runRequest(requests.get, url=url, headers=im_headers)
    if ret.status_code != 200:
        logger.error("Failed to get oss data source information!")
        return None
    else:
        data = ret.json()
        custom_endpoint = data['connection']['custom_endpoint']
        oss_access_key = data['connection']['oss_access_key']
        oss_secret_key = data['connection']['oss_secret_key']
        content_data = {
            'type': 'OSS',
            's3Endpoint': custom_endpoint,
            's3AccessKey': oss_access_key,
            's3SecretKey': oss_secret_key,
            'rootPath': '/dh-checkpoint-eu-1/DI_DATA_LAKE'
        }
        return content_data

def get_content_data_adlv2(im_base_url, im_headers):
    url = im_base_url + '/api/v1/data/connection/AZURE/ADLV2/imadlv2'
    ret = runRequest(requests.get, url=url, headers=im_headers)
    if ret.status_code != 200:
        logger.error("Failed to get oss data source information!")
        return None
    else:
        data = ret.json()
        account_key = data['connection']['account_key']
        account_name = data['connection']['account_name']
        content_data = {
            'type': 'ADL_V2',
            'adlv2SharedKeysAccountKey': account_key,
            'adlv2SharedKeysAccountName': account_name,
            'adlv2AuthorizationMethod': 'shared_key',
            'rootPath': '/imadlv2/DI_DATA_LAKE'
        }
        return content_data

def create_connection_by_type(con_config):
    content_data = None
    if con_config['connection_type'] == 'HDFS':
        con_config['connection_id'] = 'BLR_TEST_HDFS'
        con_config['description'] = 'hdfs connection created by DI CI framework'
        content_data = get_content_data_hdfs(im_base_url, im_headers)
    elif con_config['connection_type'] == 'SDL':
        con_config['connection_id'] = 'DI_DATA_LAKE'
        con_config['description'] = 'data lake connection created by DI CI framework'
        # monsoon -> s3; gke -> gcs; azure -> s3(adlv2); eks -> s3
        get_content_dic = {'MONSOON': get_content_data_s3,
                           'AWS-EKS': get_content_data_s3,
                           'AZURE-AKS': get_content_data_adlv2,
                           'GKE': get_content_data_gcs,
                           'GARDENER-CCLOUD': get_content_data_s3,
                           'DHAAS-AWS': get_content_data_s3}
        get_content_data = get_content_dic[provision_platform]
        content_data = get_content_data(im_base_url, im_headers)
    # TODO: ABAP  # pylint: disable=fixme
    if not content_data:
        logger.error('failed to generate content_data, exit!')
        return False
    con_config['content_data'] = content_data

    return create_and_check_connection_with_retry(con_config)

if __name__ == "__main__":
    vsystem_endpoint = sys.argv[1]
    provision_platform = sys.argv[2]
    auth_im_header = sys.argv[3]
    default_tenant = sys.argv[4]
    default_username = sys.argv[5]
    default_password = sys.argv[6]
    connection_type = sys.argv[7]
    index = auth_im_header.find(': ')
    auth_key = auth_im_header[:index]
    auth_value = auth_im_header[index+2:]
    im_headers = { auth_key: auth_value }
    im_base_url = os.environ.get("SERVER_URL", 'https://im-api.datahub.only.sap')
    last_ret = False
    con_config = {}
    con_config['im_base_url'] = im_base_url
    con_config['im_headers'] = im_headers
    con_config['connection_type'] = connection_type
    con_config['vsystem_endpoint'] = vsystem_endpoint
    con_config['provision_platform'] = provision_platform
    con_config['default_tenant'] = default_tenant
    con_config['default_username'] = default_username
    con_config['default_password'] = default_password
    last_ret = create_connection_by_type(con_config)
    if not last_ret:
        exit(1)
    exit(0)
    

