# Copyright 2020-2021 SAP SE or an SAP affiliate company. All rights reserved.
import sys
import logging
import os
import urllib3
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

#pylint: disable=dangerous-default-value


def requests_retry_session(
        retries=3,
        backoff_factor=1,
        status_forcelist=list(range(500, 600)),
        session=None,
):

    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    request_retry = HTTPAdapter(max_retries=retry)
    session.mount('http://', request_retry)
    session.mount('https://', request_retry)
    return session

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def manage_dns_record_set(action, recordset_name, record_type, target_name):
    proxies = {
        "http": None,
        "https": None,
    }
    token = os.environ.get(
        'IM_TOKEN', 'askingimteamforimtokenifitsinvalid')
    header = {'Authorization': 'Bearer {}'.format(token)}
    url = 'https://im-api.datahub.only.sap/api/v1/clusters/route53/' + '/' + recordset_name
    body = {
        "type": record_type,
        "value": target_name
    }
    try:
        logging.info(
            'Start to do route53 dns registration with url ' + url + ' with info ' + str(body))
        resp = requests_retry_session().post(url,
                                            json=body,
                                            verify=False,
                                            headers=header,
                                            proxies=proxies,
                                            timeout=300)
        if resp.status_code == 200:
            logging.info(
                'Successfully registration route53 record set with resp info ' + str(resp.text))
        else:
            logging.error(
                'Failed to registration route53 record set with resp error ' + str(resp.text))
    except Exception as ex:
        logging.error(
            'Failed to registration route53 record set with exception ' + str(ex))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        logging.debug("4 args needed for this function: action, domain_name, record_set_type, target_ip_address !")
        exit(1)
    action = sys.argv[1]
    recordset_name = sys.argv[2]
    record_type = sys.argv[3]
    target_name = sys.argv[4]

    manage_dns_record_set(action, recordset_name, record_type, target_name)