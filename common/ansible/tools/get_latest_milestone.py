import requests
import os, sys
import time
import logging

check_interval = int(os.environ.get("CHECK_INTERVAL", 60))
max_error_retry_num = int(os.environ.get("MAX_ERROR_RETRY_NUM", 3))
max_refuse_time = int(os.environ.get("MAX_REFUSE_WAIT", 7200))
max_wait_ready_time = int(os.environ.get("MAX_READY_WAIT", 3600))
timestamp_str = str(int(time.time()*1000))


# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create file handler and set level to debug
log_file_path='/infrabox/output/get_latest_milestone.log'
fh = logging.FileHandler(log_file_path, mode='wb')
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

			
if __name__ == "__main__":
    base_url = os.environ.get("SERVER_URL", 'https://odtem-api.datahub.only.sap:443')
    url = base_url+'/api/v1/product/version'+'?repos_type=build.milestones'
    response = runRequest(requests.get, url)

    if response.status_code != 200:  
        sys.exit(1)
    else:
        data = response.json()
        list_data = data['dataList']
        for each in list_data:
            prod_str = each['prod_version'].encode("utf-8")
            if(sys.argv[1] == 'stable'):
                if(not prod_str.endswith('ms')):
                    print(each['prod_version'])
                    break
            elif (sys.argv[1] == 'master'):
                if( prod_str.endswith('ms')):
                    print(each['prod_version'])
                    break
        sys.exit(0)
