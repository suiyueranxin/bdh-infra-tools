#!/usr/bin/env python

import os
import os.path
import json
import time
import logging
import requests



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


def set_clutser_tag_to_web(base_url, cluster_name, header):

    rest_api_path = "/api/v1/clusters/k8s/" + cluster_name
    url = base_url + rest_api_path
    env = {"kc_tag_name" : "WEB"}

    ret = run_request(requests.patch, url, json=env, headers=header)
    if ret.status_code == 200:
        data = ret.json()
        if data["status"] == "200":
            return True

    return False

def extend_cluster(base_url, cluster_name, header, reserve_hours):

    rest_api_path = "/api/v1/clusters/k8s/" + cluster_name + "/expiration/" + reserve_hours
    url = base_url + rest_api_path

    ret = run_request(requests.patch, url,  headers=header)
    if ret.status_code == 200:
        data = ret.json()
        if data["status"] == "200":
            return True
    return False    

def get_auth_header(base_url, owner):
    if 'IM_AUTH_HEADER' in os.environ:
        token = os.environ['IM_AUTH_HEADER']
        return {'Authorization': 'Bearer {}'.format(token)}
    else:
        sys_account = os.environ.get('SYS_ACCOUNT')
        sys_password = os.environ.get('SYS_PASSWORD')
        if sys_account is None or sys_password is None:
            raise RuntimeError("Fail to generate auth header, no SYS_ACCOUNT or SYS_PASSWORD!")

        response = run_request(requests.post, base_url + '/api/v1/users/user/' + owner, data=json.dumps({"username": sys_account, "password": sys_password}))
        # try both /api/v1/users/user/ and /api/v1/user/ for backward capability
        if response.status_code != 200:
            response = run_request(requests.post, base_url + '/api/v1/user/' + owner, data=json.dumps({"username": sys_account, "password": sys_password}))
        if response.status_code != 200:
            logger.error("Can not get auth token, API server respond error!")
            raise RuntimeError("Fail to genreate auth header!")
        else:
            token = response.json().get('token')
            return {'Authorization': 'Bearer {}'.format(token)}



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
    owner = "SDHINFRA"
    base_url = get_base_url()
    header = get_auth_header(base_url, owner)
    cluster_name = os.environ.get("CLUSTER_NAME", None)
    reserve_hours = os.environ.get("RESERVE_CLUSTER", None)
    if cluster_name is None:
        logger.warning("Empty cluster name")
        exit(1)
    if reserve_hours is None:
        logger.warning("Cluster reserved hours is None")
        exit(1)   
    if set_clutser_tag_to_web(base_url, cluster_name, header) and extend_cluster(base_url, cluster_name, header, reserve_hours):
        exit(0)
    else: 
        logger.warning("### [level=warning] Reserve cluster failed")
        exit(1)
