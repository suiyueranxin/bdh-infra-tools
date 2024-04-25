import os
import json
import requests
import re
import sys

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

RETRY_TIMES = 4
CHECK_INTERVAL = 30

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    datalist.sort(key=natural_keys) sorts in human order
    '''
    return [atoi(c) for c in re.split(r'(\d+)', text)]

def get_version_list(url):
    error_num = 0
    while True:
        try:
            username = os.environ.get('CC_API_USER', '')
            password = os.environ.get('CC_API_PASSWORD', '')
            response = requests.get(
                    url,
                    auth=(username, password),
                    verify=False)
            results = json.loads(response.content.decode('utf-8'))
            res = results.get('tags') or []
            versions = list(set(res))
            versions.sort(key=natural_keys, reverse=True)
            return versions
        except Exception as err:
            error_num = error_num + 1
            # retry for RETRY_TIMES
            if error_num < RETRY_TIMES:
                time.sleep(CHECK_INTERVAL)
            else:
                return []

def get_branch_version(version_list, branch, cfg_version):
    try:
        if cfg_version in version_list:
            return cfg_version
        elif branch == 'master':
            return version_list[0]
        elif branch.find('rel-') == 0:
            version_prefix = branch.strip('rel-')
            brach_version_list = [s for s in version_list if (s.startswith(version_prefix)) and (not s.endswith('0'))]
            if brach_version_list:
                return brach_version_list[0]

        return None
    except Exception as err:
        raise err

def run(branch, cfg_version):
    docker_url='https://public.int.repositories.cloud.sap/v2/com.sap.datahub.linuxx86_64/di-platform-full-product-bridge/tags/list'
    version_list = get_version_list(docker_url)
    if not version_list:
        print('please check the version_list got from docker.wdf.sap.corp is []')
        return cfg_version
    return get_branch_version(version_list, branch, cfg_version)

if __name__ == '__main__':
    branch=sys.argv[1]
    cfg_version=sys.argv[2]
    branch_version=run(branch, cfg_version)
    if branch_version:
        print('branch_version='+ branch_version)

