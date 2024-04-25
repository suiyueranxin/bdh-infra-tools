import os
import sys
import json
import logging
import requests
from copy import deepcopy
import threading

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

use_for = os.getenv('USE_FOR', None)
ccm_jobs_file = os.path.join(os.getcwd(), 'smoke_tests_jobs_CCM.json')
dwc_jobs_file = os.path.join(os.getcwd(), 'smoke_tests_jobs_DWC.json')
hc_jobs_file = os.path.join(os.getcwd(), 'smoke_tests_jobs_HC.json')
metadata_file_path = '/project/dis_metadata'
get_metadata_sh = os.path.join(os.getcwd(), 'get_metadata_file.sh')
env_file = '/infrabox/output/env.sh'
image_cache = {}
metadata_cache = {}


def format_service_plan(input_service_plan):
    if input_service_plan.endswith('_CCM'):
        return 'ccm'
    elif input_service_plan.endswith('_DWC'):
        return 'dwc'
    elif input_service_plan.endswith('_HC'):
        return 'hc'


def get_test_plans():
    test_plans = []
    jobs_files = [ccm_jobs_file, dwc_jobs_file, hc_jobs_file]
    for jobs_file in jobs_files:
        if not os.path.exists(jobs_file):
            logger.warning('Test path file does not exist, please check!')
            sys.exit(1)
        with open(jobs_file, 'r') as f:
            content = json.load(f)
            test_plans.append(content['jobs'])
    return test_plans


def registerToRestAPI(restAPIHost, restAPIPort, restAPIPath, jsonObj):
    if not restAPIPort:
        url = restAPIHost + restAPIPath
    else:
        url = restAPIHost + ':' + restAPIPort + restAPIPath
    retry = 1
    sendSuccess = False
    while retry <= 3:
        logger.info("Try to sendTestMetadataToRestApi: [" + str(retry) + "/3]")
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


def get_metadata_from_image(image, tag, job, metadata_config=None):
    if job in metadata_cache:
        return metadata_cache[job]['suites'], metadata_cache[job]['metadata_correct']
    test_suites = []
    metadata_correct = True
    get_metadata_cmd = get_metadata_sh + ' ' + image + ' ' + tag.strip() + ' ' + job
    if metadata_config is not None:
        get_metadata_cmd += ' ' + metadata_config
    logger.info('Get metadata cmd is:' + get_metadata_cmd)
    job_metadata_file_path = os.path.join(metadata_file_path, job)
    if not os.path.exists(job_metadata_file_path):
        os.mkdir(job_metadata_file_path)
    os.system(get_metadata_cmd)
    for path, dir_list, file_list in os.walk(job_metadata_file_path):
        for file_name in file_list:
            metadata_file = os.path.join(path, file_name)
            ret = os.system("metadata_checker " + metadata_file)
            if ret != 0:
                metadata_correct = False
            test_metadata = None
            with open(metadata_file, 'r') as f:
                test_metadata = json.load(f)
                for suite in test_metadata['suites']:
                    if 'production_type' not in suite or suite['production_type'] != "DI:E":
                        continue
                    test_suites.append(suite)
    metadata_cache[job] = {
        'suites': test_suites,
        'metadata_correct': metadata_correct
    }
    return test_suites, metadata_correct


def parse_dis_test_jobs(test_plans):
    if not isinstance(test_plans, list):
        logger.warning("test plan should be a list")
        return None
    infrabox_job_info = json.load(open('/infrabox/job.json', 'r'))
    register_datas = []
    for test_plan in test_plans:
        register_body = {
            'environment': {},
            'test_jobs': []
        }
        if 'job' in infrabox_job_info:
            register_body['job'] = infrabox_job_info['job']
        if 'project' in infrabox_job_info:
            register_body['project'] = infrabox_job_info['project']
        if 'build' in infrabox_job_info:
            register_body['build'] = infrabox_job_info['build']
        if 'commit' in infrabox_job_info:
            register_body['commit'] = infrabox_job_info['commit']
        register_body['environment']['GERRIT_CHANGE_PROJECT'] = os.getenv('GERRIT_PROJECT', 'dis-release')
        register_body['environment']['NAMESPACE'] = os.getenv('NAMESPACE', 'datahub')
        register_body['environment']['INFRABOX_BUILD_RESTART_COUNTER'] = os.getenv('INFRABOX_BUILD_RESTART_COUNTER', '1')
        register_body['environment']['DIS_VERSION'] = os.getenv('DIS_VERSION')
        register_body['environment']['PR_NUMBER'] = os.getenv('GITHUB_PULL_REQUEST_NUMBER')
        register_body['environment']['SERVICE_PLAN'] = format_service_plan(test_plan[0]['environment']['SERVICE_PLAN'])
        register_body['environment']['USE_FOR'] = use_for
        register_body['environment']['JOB_NAME'] = register_body['job']['name']
        register_body['environment']['GERRIT_CHANGE_BRANCH'] = os.getenv('GERRIT_CHANGE_BRANCH')
        landscape = os.getenv('LANDSCAPE')
        if landscape:
            register_body['environment']['LANDSCAPE'] = landscape[:landscape.rfind("-")]
        register_body['test_jobs'] = []
        for test in test_plan:
            if 'COMPONENT' in test['environment']:
                component = test['environment']['COMPONENT']
                tag = os.getenv(component + "_VERSION")
            if 'COM_DOCKER_IMAGE' in test['environment']:
                job_test_image = test['environment']['COM_DOCKER_IMAGE']
            if 'METADATA_CONFIG' in test['environment']:
                metadata_config = test['environment']['METADATA_CONFIG']
            job_info = {
                'job_name': test['name'],
                'service_plan': format_service_plan(test['environment']['SERVICE_PLAN']),
                'test_job_name': test['name'],
                'component': component,
                'suites': []
            }
            if job_test_image is not None and tag is not None:
                suites, metadata_correction = get_metadata_from_image(job_test_image, tag, job_info['test_job_name'],
                                                                      metadata_config=None)
                job_info['job_metadata_correct'] = 'true' if metadata_correction else 'false'
                if suites:
                    if metadata_correction:
                        job_info['suites'] = suites
                        register_body['test_jobs'].append(job_info)
                    else:
                        logger.warning('Metadata file of job ' + job_info[
                            'job_name'] + ' is incorrect and metadata will not registered to dashboard!')
        print('###Register body for dis:')
        print (json.dumps(register_body, indent=4, sort_keys=True))
        logger.info("Saving the request json to Archive")
        with open('/infrabox/upload/archive/' + register_body['environment'][
            'SERVICE_PLAN'] + '_dis_register_json_data.json', 'w') as outfile:
            json.dump(register_body, outfile)
        register_datas.append(register_body)

    not_registered_jobs = {}
    with open('/infrabox/upload/archive/dis_not_registered_jobs.txt', 'w') as f:
        for job in metadata_cache.keys():
            if metadata_cache[job]['suites']:
                f.write(job + '\n')
                not_registered_jobs[job] = deepcopy(metadata_cache[job])
    with open('/infrabox/upload/archive/test_metadata_not_registered.json', 'w') as nf:
        json.dump(not_registered_jobs, nf)

    # parallel to register metadata
    logger.info("### Start registering dis test metadate to dashboard REST API in parallel")
    restAPIHost = os.environ.get('RESTAPI_HOST', 'https://api.dashboard.datahub.only.sap')
    restAPIPort = os.environ.get('RESTAPI_PORT', '30711')
    restAPIPath = os.environ.get('RESTAPI_PATH', '/api/v1/dis/register')
    threads = []
    for register_data in register_datas:
        thread = threading.Thread(target=registerToRestAPI, args=[restAPIHost, restAPIPort, restAPIPath, register_data])
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    if use_for is None:
        logger.warning("use_for is invalid")
        sys.exit(1)
    test_plans = get_test_plans()
    parse_dis_test_jobs(test_plans)
