import requests
import os, sys
import json
import time
import logging

check_interval = int(os.environ.get("CHECK_INTERVAL", 60))
max_error_retry_num = int(os.environ.get("MAX_ERROR_RETRY_NUM", 3))
max_refuse_time = int(os.environ.get("MAX_REFUSE_WAIT", 7200))
max_wait_ready_time = int(os.environ.get("MAX_READY_WAIT", 3600))
timestamp_str = str(int(time.time()*1000))


# create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create file handler and set level to debug
log_file_path='/infrabox/output/get_cloud_credentials.log'
fh = logging.FileHandler(log_file_path, mode='w')
fh.setLevel(logging.INFO)
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

if __name__ == "__main__":
    cluster_name = sys.argv[1]
    provision_platform = sys.argv[2]
    base_path = sys.argv[3]
    auth_header = sys.argv[4]
    api_path = '/api/v1/configs/crdls/push_validation'
    if len(sys.argv) >= 6:
        api_path = '/api/v1/configs/crdls/' + sys.argv[5]
    index = auth_header.find(': ')
    auth_key = auth_header[:index]
    auth_value = auth_header[index+2:]
    header = { auth_key: auth_value }
    if provision_platform == "GARDENER-CCLOUD":
        logging.info("for GARDENER-CCLOUD we don't need to generate the credential file. ")
        sys.exit(0)
    else:
        base_url = os.environ.get("SERVER_URL", 'https://im-api.datahub.only.sap')
        url = base_url + api_path
        logger.info("Get gke credential with url %s" % url)
        
        error_num = 0
        while True:
            response = runRequest(requests.get, url, headers=header)
            if response.status_code not in [200, 201]:
                logger.warning( "Request gke credential status_code is {}".format(response.status_code))

                error_num = error_num + 1
                # retry for max_error_retry_num
                if error_num < max_error_retry_num:
                    logger.info( "Wait for %d seconds and retry" % check_interval)
                    time.sleep(check_interval)
                else:
                    logger.error( "Fail to get gke credential for %d seconds!" % max_error_retry_num)
                    sys.exit(1)        
            else:
                data = response.json()
                credentials=data['credentials']
                credential_json = {}
                if provision_platform == "GKE":
                    provision_platform = "GCP-GKE"
                try:
                    credential_json = credentials[provision_platform]['registry_full_access']
                except KeyError:
                    logger.error("No credential for platform:" + provision_platform)
                    sys.exit(1)
                with open(os.path.join(base_path, 'credential.json'), 'w') as out_file:
                    json.dump(credential_json, out_file)
                sys.exit(0)

