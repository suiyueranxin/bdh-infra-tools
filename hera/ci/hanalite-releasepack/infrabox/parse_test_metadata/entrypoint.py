import os
import sys
import json
import logging
import requests
from copy import deepcopy
import concurrent.futures
import threading
from junit_xml import TestSuite, TestCase

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

test_cycle_file_path = os.path.join('TestCycleConfiguration','TestCycle.json')
test_plan_file_path = os.path.join('TestCycleConfiguration','TestPlans.json')
releasepack_path = os.path.join(os.getcwd(), 'hanalite-releasepack')
deploy_type = os.getenv('DEPLOY_TYPE', None)
use_for = os.getenv('USE_FOR', None)
validation_job_file = os.path.join(os.getcwd(), 'validation_jobs.json')
metadata_file_path = '/project/metadata'
get_metadata_sh = os.path.join(os.getcwd(), 'get_metadata_file.sh')
env_file = '/infrabox/output/env.sh'
image_cache = {}
cases = []
platform_map = {
    'DHAAS-AWS': 'dhaas_aws',
    'AWS-EKS': 'eks',
    'AZURE-AKS': 'aks',
    'GKE': 'gke'
}
platform_map_reverse = {
    'EKS': 'AWS-EKS',
    'AKS': 'AZURE-AKS',
    'GKE': 'GKE'
}
metadata_cache = {}
REGISTER_RESULT = {
    'success': [],
    'fail': []
}
job_white_list = [
    'vsystem_integration_test', 
    'connection_mgmt_ui_e2e_test', 
    'customer_data_export_ui_e2e_test', 
    'monitoring_ui_e2e_test', 
    'datahub_app_data_metadata_e2e_test',
    'datahub_app_base_test',
    'datahub_app_data_test',
    'vsystem_ui_e2e_test',
    'launchpad_ui_e2e_test',
    'vflow_modeler_core_ui_e2e_test',
    'vflow_modeler_extended_ui_e2e_test',
    'vora_tools_ui_e2e_test',
    'vflow_datahub_dq_integration_test',
    'e2e_vora_test',
    'e2e_mats_core_test',
    'e2e_mats_metadata_test',
    'e2e_scenario_test',
    'e2e_smoke_core_test',
    'e2e_smoke_metadata_test',
    'vflow_flowagent_test',
    'diagnostics_test',
    'e2e_smoke_metadata_test',
    'vflow_flowagent_test',
    'diagnostics_test',
    'dsp_acceptance_test',
    'vflow_test'
]
def get_test_cycles():
    test_cycle_file = os.path.join(releasepack_path, test_cycle_file_path)
    if not os.path.exists(test_cycle_file):
        logger.warning('Test cycle file does not exist, please check!')
        sys.exit(1)
    test_plans_from_cycle = []
    cur_type = use_for.upper() + '_' + deploy_type.lower()
    if use_for == "MILESTONE_VALIDATION_preview":
        cur_type = "MILESTONE_VALIDATION_" + deploy_type.lower()
    with open(test_cycle_file, 'r') as f:
        cycles = json.load(f)
        for cycle in cycles['cycles']:
            if 'type' in cycle and cycle['type'] == cur_type:
                if 'plans' in cycle:
                    test_plans_from_cycle += cycle['plans']
                break
    return test_plans_from_cycle

def get_test_plans():
    test_plans_from_cycle = get_test_cycles()
    test_plan_file = os.path.join(releasepack_path, test_plan_file_path)
    if not os.path.exists(test_plan_file):
        logger.warning('Test plan file does not exist, please check!')
        sys.exit(1)    
    test_plans = {}
    if use_for == 'MILESTONE_VALIDATION_e2e':
        path = os.path.join(os.getcwd() , 'job.json')
        if not os.path.exists(path):
            logger.warning('Test plan file does not exist, please check!')
            sys.exit(1) 
        with open(path, 'r') as f:
            test_plans = json.load(f)
    else:
        with open(test_plan_file, 'r') as f:
            plans = json.load(f)
            for plan in plans['plans']:
                if len(test_plans_from_cycle) == 0:
                    break
                if 'name' in plan and plan['name'] in test_plans_from_cycle:
                    test_plans_from_cycle.remove(plan['name'])
                    if 'platforms' in plan and 'tests' in plan:
                        for plat in plan['platforms']:
                            if plat in test_plans:
                                test_plans[plat] += plan['tests']
                            else:
                                test_plans[plat] = plan['tests']

    print('###Test plans: ')
    print(json.dumps(test_plans, indent=4, sort_keys=True))
    return test_plans


def get_component_image_tag(component_name):
    logger.info("current component: " + component_name)
    tag = None
    if not image_cache:
        if not os.path.exists(env_file):
            logger.warning('env file does not exist')
            return tag
        with open(env_file, 'r') as f:
            for line in f.readlines():
                cur_component = str(str(line.split('=')[0]).split(' ')[1])[:-8]
                image_cache[cur_component] = line.split('=')[1]
                if line.startswith('export ' + component_name + '_VERSION='):
                    tag = line.split('=')[1]
    else:
        if component_name in image_cache:
            tag = image_cache[component_name]
    return tag

def get_test_job_info(test_job_name):
    job_test_image, tag, component, metadata_config = None, None, None, None
    logger.info("current test job: " + test_job_name)
    with open(validation_job_file, 'r') as f:
        jobs = json.load(f)
        for job in jobs['jobs']:
            if job['name'] == test_job_name and job['type'] == 'docker-image' and 'environment' in job:
                if 'COMPONENT' in job['environment']:
                    component =  job['environment']['COMPONENT']
                    if component == 'RELEASEPACK':
                        tag = os.getenv('VORA_VERSION')
                    else:
                        tag = get_component_image_tag(component)
                if 'COM_DOCKER_IMAGE' in job['environment']: 
                    job_test_image = job['environment']['COM_DOCKER_IMAGE']
                if 'METADATA_CONFIG' in job['environment']:
                    metadata_config = job['environment']['METADATA_CONFIG']
                break
    return job_test_image, tag, component, metadata_config

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
            result = json.loads(ret.content.decode())
            REGISTER_RESULT['success'] += deepcopy(result["dataList"]["success registered jobs"])
            REGISTER_RESULT['fail'] += deepcopy(result["dataList"]["failed registered jobs"])
            break
        retry += 1
    if not sendSuccess:
        raise Exception("send test metadata to restApi failed in 3 times, will exit")

def get_metadata_from_image(image, tag, job, metadata_config):
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
                    if 'production_type' in suite and suite.get('production_type', '') != "DI:Full":
                        continue
                    if 'platform' in suite:
                        suite['platform']=[platform_map[platform] if platform in platform_map else platform for platform in suite['platform']]
                    for case in suite['cases']:
                        if 'skip' in case and 'platform' in case['skip']:
                            case['skip']['platform'] = [platform_map[platform] if platform in platform_map else platform for platform in case['skip']['platform']]
                    test_suites.append(suite)
    metadata_cache[job] = {
        'suites': test_suites,
        'metadata_correct': metadata_correct
    }
    return test_suites, metadata_correct

def parse_test_jobs(test_plans):
    if not isinstance(test_plans, dict):
        logger.warning("test plan should be a dict")
        return None
    
    platforms = test_plans.keys()
    if deploy_type == "on_premise":
        platforms = [platform_map_reverse[x.upper()] for x in eval(str(os.environ.get("MS_PLATFORM", '[]')))]
    full_platform = [platform_map[x.upper()] for x in platforms]
    infrabox_job_info = json.load(open('/infrabox/job.json', 'r'))
    register_data = {}
    # parse metadate for single job
    def target(test_job):
        if 'infrabox_job' in test_job and test_job['infrabox_job'] in job_white_list:
            job_test_image, tag, component, metadata_config= get_test_job_info(test_job['infrabox_job'])
            job_info = {
                'job_name': test_job['infrabox_job'] + '_' + platform_registed,
                'test_job_platform': platform_registed,
                'test_job_name': test_job['infrabox_job'],
                'component': component,
                'suites': []                   
            }
            if job_test_image is not None and tag is not None:
                suites, metadata_correction = get_metadata_from_image(job_test_image, tag, job_info['test_job_name'], metadata_config)
                job_info['job_metadata_correct'] = 'true' if metadata_correction else 'false'
                if suites:
                    if metadata_correction:
                        job_info['suites'] = suites
                        register_body['test_jobs'].append(job_info)
                    else:
                        logger.warning('Metadata file of job ' + job_info['job_name'] + ' is incorrect and metadata will not registered to dashboard!')
                        case = TestCase(test_job['infrabox_job'] , "metadata_check_failed_jobs")
                        case.add_failure_info(test_job['infrabox_job'] + " metadata_check_failed_jobs")
                        cases.append(case)
                        #TBD: send email to someone
    # parse metadata for each platform  
    for platform in platforms:
        platform_registed = platform_map[platform.upper()]
        register_body = {
            'environment': {'full_platform': full_platform},       
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
        register_body['environment']['GERRIT_CHANGE_PROJECT'] = os.getenv('GERRIT_CHANGE_PROJECT', 'hanalite-releasepack')
        register_body['environment']['INFRABOX_BUILD_RESTART_COUNTER'] = os.getenv('INFRABOX_BUILD_RESTART_COUNTER', '1')
        register_body['environment']['NAMESPACE'] = os.getenv('NAMESPACE', 'datahub')
        register_body['environment']['JOB_PLATFORM'] = platform_registed
        register_body['environment']['USE_FOR'] = use_for
        register_body['environment']['JOB_NAME'] = register_body['job']['name']
        register_body['environment']['DEPLOY_TYPE'] = deploy_type
        register_body['environment']['VORA_VERSION'] = os.getenv('VORA_VERSION')
        register_body['environment']['GERRIT_CHANGE_BRANCH'] = os.getenv('GERRIT_CHANGE_BRANCH')
        register_body['test_jobs'] = []
        # parse metadata for jobs in parallel
        logger.info("### parse metadata for jobs in parallel")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            executor.map(target, test_plans[platform])
        print('###Register body for ' + platform + ':')
        print(json.dumps(register_body, indent=4, sort_keys=True))
        logger.info("Saving the request json to Archive")
        with open('/infrabox/upload/archive/' + platform_registed + '_registe_json_data.json', 'w') as outfile:
            json.dump(register_body, outfile)
        register_data[platform] = register_body

    not_registered_jobs = {}
    with open('/infrabox/upload/archive/not_registered_jobs.txt', 'w') as f:
        for job in metadata_cache.keys():
            if job not in job_white_list and metadata_cache[job]['suites']:
                f.write(job + '\n')
                not_registered_jobs[job] = deepcopy(metadata_cache[job])
    with open('/infrabox/upload/archive/test_metadata_not_registered.json', 'w') as nf:
        json.dump(not_registered_jobs, nf)
    
    logger.info("### Start registering test metadata to dashboard")
    restAPIHost = os.environ.get('RESTAPI_HOST', 'https://api.dashboard.datahub.only.sap')
    restAPIPort = os.environ.get('RESTAPI_PORT', '30711')
    restAPIPath = os.environ.get('RESTAPI_PATH', '/api/v1/trd/register')
    for platform in platforms:
        if platform in register_data:
            registerToRestAPI(restAPIHost, restAPIPort, restAPIPath, register_data[platform])

if __name__ == '__main__':
    if deploy_type is None or use_for is None:
        logger.warning("deploy_type or use_for is invalid")
        sys.exit(1)
    test_plans = get_test_plans()
    parse_test_jobs(test_plans)
    for job in REGISTER_RESULT['success']:
        case = TestCase(job, "registered_jobs")
        cases.append(case)

    for job in REGISTER_RESULT['fail']:
        case = TestCase(job, "registered_jobs")
        case.add_failure_info(job + " register to dashboard failed")
        cases.append(case)

    suite = TestSuite("Metadata register", cases)
    with open('/infrabox/upload/testresult/metadata_register_result.xml', 'w') as f:
        TestSuite.to_file(f, [suite])
