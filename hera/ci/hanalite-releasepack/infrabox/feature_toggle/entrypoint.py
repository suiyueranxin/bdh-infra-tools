import os
import sys
import json
import logging
import requests
import subprocess
import re
from copy import deepcopy

# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(lineno)d - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
class FeatureToggle(object):
    def __init__(self, tenant=None,tenant_user=None,tenant_password=None):
        needed_envs=['VSYSTEM_ENDPOINT','VORA_SYSTEM_TENANT_PASSWORD']
        for env in needed_envs:
            if env not in os.environ:
                logger.error(env + " is missing in system env variable, please check")
                sys.exit(1)
        self.system_end_point = os.getenv('VSYSTEM_ENDPOINT', None)
        self.system_tenant = os.getenv('VORA_SYSTEM_TENANT', 'system')
        self.system_tenant_user = 'system'
        self.system_tenant_password = os.getenv('VORA_SYSTEM_TENANT_PASSWORD', None)
        # if there is $ in password, password will be invliad, add password in '' to avoid this issue
        self.system_tenant_password = '\'' + self.system_tenant_password + '\'' 
        self.default_tenant = os.getenv('VORA_TENANT', 'default')
        #self.system_tenant = 'adfeadf'
        if not self.__login_system_tenant():
            logger.error("Initial failed, login system tenant failed!")
            sys.exit(1)
    def __login_system_tenant(self):
        cmd = 'vctl login ' + self.system_end_point + ' '+ self.system_tenant +' ' + self.system_tenant_user + ' -p ' + self.system_tenant_password + ' --insecure'
        print(cmd)
        p = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err=p.communicate()
        if p.returncode == 0:
            return True
        else:
            logger.error("Login system tenant failed, reason: " + err)
            return False
    def get_feature_toggles(self):
        p = subprocess.Popen('vctl feature list --tenant ' + self.default_tenant + ' -o json', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err=p.communicate()
        if p.returncode != 0:
            logger.error("Get feature toggle list failed, reason: " + err)
            return None
        feature_toggles = json.loads(out)
        return feature_toggles
    def enable_feature(self, toggle_id, tenant='default'):
        cur_tenant = tenant
        p = subprocess.Popen('vctl feature enable ' + cur_tenant + ' ' + toggle_id, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err=p.communicate()
        if p.returncode != 0:
            logger.error("Enable flag " + toggle_id + " failed, failed reason: " + err)
            return False, err
        return True, out
    def disable_feature(self, toggle_id, tenant='default'):
        cur_tenant = tenant
        p = subprocess.Popen('vctl feature disable ' + cur_tenant + ' ' + toggle_id, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err=p.communicate()
        if p.returncode != 0:
            logger.error("Enable flag " + toggle_id + " failed, failed reason: " + err)
            return False, err
        return True, out
    def get_user_story(self, toggle_id, tenant='default'):
        return []
def registerToRestAPI(restAPIHost, restAPIPort, restAPIPath, jsonObj):
    if not restAPIPort:
        url = restAPIHost + restAPIPath
    else:
        url = restAPIHost + ':' + restAPIPort + restAPIPath
    retry = 1
    sendSuccess = False
    while retry <= 3:
        logger.info("Try to sendTestMetadataToRestApi: [" + str(retry) +"/3]")
        ret = requests.post(url, verify=False, json=jsonObj)
        logger.info("sendTestMetadataToRestAPI response code: " + str(ret.status_code))
        logger.info("sendTestMetadataToRestAPI response content: " + str(ret.content))
        if ret.status_code in [200, 201]:
            logger.info("sendTestMetadataToRestApi success")
            sendSuccess = True
            break
        retry += 1
    if not sendSuccess:
        raise Exception("send test metadata to restApi failed in 3 times, will exit")

if __name__ == '__main__':
    feature_toggle =  FeatureToggle()
    feature_toggle_settings = os.environ.get('FEATURE_TOGGLES', None) 
    if feature_toggle_settings:
        feature_toggle_settings = feature_toggle_settings.strip()
        feature_toggles_list = feature_toggle_settings.split(';')
        for toggle in feature_toggles_list:
            if toggle.find(':') > 0:
                toggle_key = toggle.split(':')[0]
                toggle_value = toggle.split(':')[1].lower()
                res = True
                msg = ''
                if toggle_value == 'true':
                    res, msg = feature_toggle.enable_feature(toggle_key)
                elif toggle_value == 'false':
                    res, msg = feature_toggle.disable_feature(toggle_key)
                if res == False:
                    logger.error("### [level=error] Set toggle: " + toggle_key + " Failed. Error: " + msg)
                    sys.exit(1)
                else:
                    logger.info("Set toggle: " + toggle_key + " successful. Message: " + msg)
    disable_register = feature_toggle_settings = os.environ.get('DISABLE_REGISTER_FF', None)
    if disable_register != 'true':
        feature_toggle_list = feature_toggle.get_feature_toggles()
        for toggle in feature_toggle_list:

            toggle['user_story'] = []
            if 'userStory' in toggle and toggle['userStory'] is not None:
                toggle['user_story'] = toggle['userStory'].split(',')

        register_body = {
            'environment': {
                'GERRIT_CHANGE_PROJECT': os.getenv('GERRIT_CHANGE_PROJECT', 'hanalite-releasepack'),
                'USE_FOR': os.getenv('USE_FOR', 'MILESTONE_VALIDATION'),
                'VORA_VERSION': os.getenv('RELEASEPACK_VERSION'),
                'PROJECT': 'milestone-validation',
                'GERRIT_CHANGE_BRANCH': os.getenv('CODELINE','master')
                },
            'feature_toggles': feature_toggle_list
            }
        print (json.dumps(register_body, indent=4, sort_keys=True))
        logger.info("Saving the request json to Archive:")
        with open('/infrabox/upload/archive/feature_toggles.json', 'w') as outfile:
            json.dump(register_body, outfile)
        restAPIHost = os.environ.get('RESTAPI_HOST', 'https://api.dashboard.datahub.only.sap')
        restAPIPort = os.environ.get('RESTAPI_PORT', '30711')
        restAPIPath = os.environ.get('RESTAPI_PATH', '/api/v1/trd/featureFlag')
        registerToRestAPI(restAPIHost, restAPIPort, restAPIPath, register_body)
    


