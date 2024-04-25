"""
1. clone and read TestPlans.json
2. Read the test job template from job template detail
3. Read the job dependency
4. Assemble the complete infrabox.json
"""
import os
import json
from copy import deepcopy
import logging
from git import Repo
import pandas as pd
import numpy as np
import shutil

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


class AssembleInfraboxJson(object):
    current_path = os.path.dirname(os.path.realpath(__file__))
    codeline = ''
    releasepack_version = ''
    releasepack_refs = None

    cycle_name = {
        "on_cloud": "MILESTONE_VALIDATION_on_cloud",
        "on_premise": "MILESTONE_VALIDATION_on_premise"
    }
    platform_folder = {
        'AKS': 'aks',
        'EKS': 'eks',
        'GKE': 'gke',
        'MONSOON': 'monsoon',
        'DHAAS-AWS': 'dhaas_aws'
    }
    # deploy_typ: on_premise or on_cloud
    _on_cloud_type = 'on_cloud'
    _on_premise_type = 'on_premise'
    deploy_type = ''
    group_number = {}
    _full_platform = ''
    _test_plan_folder = os.path.join('hanalite-releasepack',
                                     'TestCycleConfiguration')
    _test_cycle_file = os.path.join(_test_plan_folder, 'TestCycle.json')
    _test_plan_file = os.path.join(_test_plan_folder, 'TestPlans.json')
    _template_detail_folder = os.path.join('database', 'temp_details')
    _template_detail_file = os.path.join(_template_detail_folder,
                                         'validation_jobs.json')
    _common_template_json_file_name = 'common.json'
    _use_for = 'MILESTONE_VALIDATION'

    def __init__(self):
        pass

    @classmethod
    def get_use_for(cls):
        return cls._use_for

    @classmethod
    def set_use_for(cls, use_for):
        cls._use_for = use_for

    @classmethod
    def get_full_platform(cls):
        return cls._full_platform

    @classmethod
    def set_full_platform(cls, full_platform):
        cls._full_platform = full_platform

    @classmethod
    def clone(cls, repo, path):
        if repo is None:
            raise ValueError('repository is None')
        if path is None:
            raise ValueError('clone path is None')
        repo = Repo.clone_from(repo, path, branch=cls.codeline)
        if cls.releasepack_refs is not None:
            repo.remotes.origin.fetch(refspec=cls.releasepack_refs)
            repo.git.checkout('FETCH_HEAD')
            return
        for tag in repo.tags:
            if tag.name.find(cls.releasepack_version.lower()) != -1 and cls.codeline == 'master' and (tag.name.find('ms') != -1 or tag.name.endswith('0')):
                repo.git.checkout(tag.name)
                break

    @classmethod
    def get_neat_platform(cls, platform):
        if platform.lower() == 'dhaas_aws':
            neat_platform = 'dhaas_aws'
        else:
            neat_platform = platform.lower().rsplit('_', 1)[0]
        return neat_platform

    @classmethod
    def get_platform(cls, platform):
        platform = cls.get_neat_platform(platform).upper()
        if platform == 'GKE':
            platform = platform_full = 'GKE'
        if platform == 'MONSOON':
            platform = platform_full = 'MONSOON'
        if platform in ['AKS', 'AZURE-AKS']:
            platform, platform_full = 'AKS', 'AZURE-AKS'
        if platform in ['EKS', 'AWS-EKS']:
            platform,  platform_full = 'EKS', 'AWS-EKS'
        if platform in ['DHAAS_AWS', 'DHAAS-AWS']:
            platform,  platform_full = 'DHAAS_AWS', 'DHAAS-AWS'
        return platform, platform_full

    @classmethod
    def convert_platform(cls, platform, returnShort=True):
        platform_dic = {
            'AZURE-AKS': 'AKS',
            'AWS-EKS': 'EKS',
            'DHAAS-AWS': 'DHAAS_AWS',
            'GKE': 'GKE',
            'MONSOON': 'MONSOON'
        }
        if returnShort:
            nt = cls.get_neat_platform(platform).upper()
            if nt in platform_dic:
                platform = platform.replace(nt, platform_dic[nt])
        else:
            revert = dict(zip(platform_dic.values(),platform_dic.keys()))
            nt = cls.get_neat_platform(platform).upper()
            if nt in revert:
                platform = platform.replace(nt, revert[nt])
        return platform

    @classmethod
    def get_neat_job_name(cls, job):
        if 'dhaas_aws' not in job.lower():
            return job.lower().rsplit('_', 1)[0]
        else:
            return job.lower().replace('dhaas_aws', '', 1)

    @classmethod
    def get_plans_by_cycle(cls, cycle_name, obj):
        for item in obj:
            if item['type'] == cycle_name:
                return item['plans']

        return None

    @classmethod
    def get_test_plan_by_plan_name(cls, plan_name, obj):
        """
        return: test plan dic.Ee.g: {'platform': {'job_name': 'job_env'},
                                    'independent': True}
        """
        # job_list save the job names and environment in the single test plan
        job_list = {}
        # plan_by_platform save the {platform: [job_list]}
        plan_by_platform = {}
        for item in obj:
            if item['name'] == plan_name:
                for job in item['tests']:
                    if 'environment' in job.keys() \
                      and len(job['environment']) != 0:
                        job_list[job['infrabox_job']] = job['environment']
                    else:
                        # set job env to empyt {}
                        job_list[job['infrabox_job']] = {}
                for platform in item['platforms']:
                    plan_by_platform[platform] = deepcopy(job_list)
                    # plan_by_platform[platform].append(job_list)
                    if 'independent' in item.keys() and item['independent'] is True:
                        plan_by_platform['independent'] = True
        return plan_by_platform

    @classmethod
    def update_test_plan_with_group_id(cls, testplan):
        """
        return: the test plan with platform_groupid as key in testplan dic
        Note: the 'independent' in original testplan dic will be removed
              The group_number will be update in this func
        """
        if 'independent' in testplan.keys() and testplan['independent'] is True:
            testplan.pop('independent', None)
        testplan_refresh = {}
        for platform in testplan:
            platform, platform_full = cls.get_platform(platform)
            cls.group_number[platform.upper()] += 1
            testplan_refresh[platform_full + '_' + str(cls.group_number[platform.upper()])] = \
                testplan[platform_full]

        return testplan_refresh

    @classmethod
    def read_test_plans(cls):
        """
        read the TestPlans.json and TestCycle.json from releasepack
        return the testplans with format:
         {
            "GKE_1": [
                {
                    "Job1": {
                        "env1": "value1",
                        "env2": "value2"
                    }
                }
            ],
            "GKE_2": [...],
            "EKS": [...]
        """
        test_plan_names = []
        with open(os.path.join(cls.current_path, cls._test_cycle_file), 'r') as f:
            cycles = json.load(f)
            test_plan_names = \
                cls.get_plans_by_cycle(cls.cycle_name[cls.deploy_type],
                                       cycles['cycles'])
        testplans = {}

        with open(os.path.join(cls.current_path, cls._test_plan_file), 'r') as f:
            plans = json.load(f)
            for item in test_plan_names:
                testplan = cls.get_test_plan_by_plan_name(item, plans['plans'])
                # update the key string(platform) with suffix
                # when independent=true
                if 'independent' in testplan.keys() and testplan['independent'] is True:
                    testplan = cls.update_test_plan_with_group_id(testplan)
                # merge the test jobs in same platform
                for key in testplan:
                    if key in testplans:
                        # add all the jobs in same platform but not in same test plan.
                        testplans[key].update(testplan[key])
                    else:
                        testplans.update(testplan)
        return testplans

    @classmethod
    def read_test_job_templete(cls):
        """
        return the validatiion template detail jobs and common template
        """
        # testjobs save the test job template detail
        # [job1, job2]
        testjobs = []
        # common_jobs save the common template jobs, k8s_creation,
        # install_<platform>...
        # {platform: [jobs]}
        common_jobs = {}
        if cls.deploy_type not in cls.cycle_name:
            raise ValueError('Request deploy_type missing. It should be on_premise or on_cloud')
        # load the validation_jobs.json for all validation jobs
        with open(os.path.join(cls.current_path, cls._template_detail_file), 'r') as f:
            testjobs = json.load(f)['jobs']

        def load_common_template(cls, folder):
            with open(os.path.join(cls.current_path,
                                   cls._template_detail_folder,
                                   folder,
                                   'common',
                                   cls._common_template_json_file_name),
                      'r') as f:
                common_tp = json.load(f)['jobs']
                return common_tp

        folders = os.listdir(os.path.join(cls.current_path,
                                          cls._template_detail_folder))
        for folder in folders:
            if os.path.isdir(os.path.join(cls.current_path,
                                          cls._template_detail_folder,
                                          folder)):
                if cls.deploy_type == cls._on_premise_type:
                    if folder != cls.platform_folder['DHAAS-AWS']:
                        common_jobs[folder.upper()] = \
                            load_common_template(cls, folder)
                else:
                    if folder == cls.platform_folder['DHAAS-AWS']:
                        common_jobs['DHAAS_AWS'] = \
                            load_common_template(cls, folder)

        # TODO: load the specified job json from each platform, # pylint: disable=W0511
        # which could overwrite the testjobs
        return testjobs, common_jobs

    @classmethod
    def insert_validation_jobs_into_common_tem(cls, testjobs, common_jobs):
        _common_jobs = deepcopy(common_jobs)
        for _, common_jobs_in_platform in _common_jobs.items():
            # infrabox_json['jobs'].append(common_jobs[platform])

            # c_job: iterate in common template
            for c_job in common_jobs_in_platform:
                if c_job['name'].startswith(('install_', 'dhaas_creation_')):
                    install_job_index = common_jobs_in_platform.index(c_job)
                    common_jobs_in_platform[install_job_index + 1:
                                            install_job_index + 1] = deepcopy(testjobs)
                    break
        return _common_jobs

    @classmethod
    def update_common_job_names(cls, merged_jobs):
        # create more template for multi group platforms
        # _job_report_job = ''
        for platform in cls.group_number:
            if platform not in merged_jobs:
                continue
            if cls.group_number[platform] > 0:
                _platform_temp = merged_jobs.pop(platform)
                for i in range(cls.group_number[platform]):
                    merged_jobs[platform + '_' + str(i + 1)] =\
                        deepcopy(_platform_temp)
                    # update job names below with group number
                    names_to_be_update = []
                    if cls.deploy_type == cls._on_premise_type:
                        names_to_be_update = ['k8s_creation', 'install',
                                              'log_collection', 'uninstall',
                                              'k8s_deletion', 'job_report']
                    elif cls.deploy_type == cls._on_cloud_type:
                        names_to_be_update = ['dhaas_creation',
                                              'log_collection',
                                              'dhaas_deletion',
                                              'job_report']
                    else:
                        raise ValueError('Request deploy_type missing. It should be on_premise or on_cloud')
                    for job in merged_jobs[platform + '_' + str(i + 1)]:
                        for prefix in range(len(names_to_be_update)):
                            if names_to_be_update[prefix] != 'job_report' \
                              and job['name'].startswith(names_to_be_update[prefix]):
                                if job['name'].lower().endswith('dhaas_aws'):
                                    string = [job['name'].replace('_dhaas_aws',''), 'dhaas_aws']
                                else:
                                    string = job['name'].rsplit('_', 1)
                                # the format would be like install_2-gke
                                string[1:1] = '_' + str(i + 1) + '-'
                                job['name'] = ''.join(string)
                            elif job['name'].startswith('job_report'):
                                pass
        return merged_jobs

    @classmethod
    def update_depends_and_job_names(cls, merged_jobs, dependency_matrix, testplans):
        def refresh_depends_on_status(cls, depends_on_list,
                                      platform,
                                      status):
            for index in range(len(depends_on_list)):
                if depends_on_list[index]['job'].endswith('test_' +
                                                          cls.get_neat_platform(platform)):
                    depends_on_list[index]['on'] = [status]

        def append_common_jobs(cls, name_list, status):
            for name in name_list:
                dep_job = {'job': name,
                           'on': [status]}
                job['depends_on'].append(dep_job)

        def update_dependency_matrix_platform(cls, dependency_matrix, testplans):
            """
            when running with multi group, the jobs in same platform name(as key) in
            dependency_matrix and testplans are not the same
            """
            temp_dependency_matrix = {}
            for platform in dependency_matrix:
                for job in dependency_matrix[platform]:
                    if cls.get_neat_job_name(job) not in testplans[cls.convert_platform(platform, False)]:
                        # the platform names are mismatch between dependency_matrix and testplans
                        # e.g: jobs in dependency_matrix['GKE_1'] are not same with testplans['GKE_1']
                        is_match = False
                        test_platform = ''
                        for test_platform in testplans:
                            if cls.get_neat_job_name(job) in testplans[test_platform]:
                                is_match = True
                                break
                        if is_match:
                            temp_dependency_matrix[test_platform] = deepcopy(dependency_matrix[platform])
                            break
                    else:
                        break
            if len(temp_dependency_matrix) > 0:
                for key in temp_dependency_matrix:
                    dependency_matrix.pop(key)
                for key in temp_dependency_matrix:
                    dependency_matrix[key] = deepcopy(temp_dependency_matrix[key])
            return dependency_matrix

        def refresh_depends_by_csv(cls, merged_jobs, dependency_matrix, testplans):
            for platform in merged_jobs:
                for i in range(len(merged_jobs[platform])):
                    job_name = merged_jobs[platform][i]['name']
                    if platform not in dependency_matrix:
                        continue
                    if job_name in dependency_matrix[platform]:
                        if len(dependency_matrix[platform][job_name]) != 0:
                            for dep_job_name in dependency_matrix[platform][job_name]:
                                # only add the job that exist in TestPlans.json
                                # the job has _<platform> in dependency.csv
                                # but don't have platform suffix in testplan
                                if platform.lower() == 'dhaas_aws':
                                    # e.g: vsystem_api_test_dhaas_aws -> vsystem_api_test
                                    dep_name_without_plat = '_'.join(dep_job_name.split('_')[:-2])
                                else:
                                    # e.g: vsystem_api_test_gke -> vsystem_api_test
                                    dep_name_without_plat = '_'.join(dep_job_name.split('_')[:-1])
                                if dep_name_without_plat in testplans[cls.convert_platform(platform, False)]:
                                    dep_job = {'job': '', 'on': ['*']}
                                    dep_job['job'] = dep_job_name
                                    merged_jobs[platform][i]['depends_on'].append(dep_job)

        # remove the undefined jobs(not defined in TestPlans.json) from merged_jobs
        cls.filter_jobs_and_update_env_by_testplans(merged_jobs, testplans)

        for platform in merged_jobs:
            if cls.deploy_type == cls._on_premise_type:
                _common_job_names = {
                    'k8s_creation': '',
                    'install': '',
                    'log_collection': '',
                    'uninstall': '',
                    'k8s_deletion': ''
                }
            else:
                _common_job_names = {
                    'dhaas_creation': '',
                    'log_collection': '',
                    'dhaas_deletion': ''
                }

            # find the common job names with platform
            # save to _common_job_names
            for job in merged_jobs[platform]:
                # clean all depends_on
                job.pop('depends_on', None)
                # init _common_job_names
                for name in _common_job_names:
                    if job['name'].startswith(name) \
                      and not job['name'].endswith('test'):
                        _common_job_names[name] = job['name']

            # only save the "_test" job
            # in to _all_jobs_in_one_platform
            _all_jobs_in_one_platform = []
            for job in merged_jobs[platform]:
                if 'environment' not in job:
                    job['environment'] = {}
                is_common_job = False
                for _, full in _common_job_names.items():
                    if job['name'] == full \
                      or job['name'].startswith('job_report'):
                        is_common_job = True
                        break
                if is_common_job is False:
                    # add platform suffix to depens_on names
                    # also update the job name with platform suffix.
                    # e.g: vsystem_api_test -> vsystem_api_test_gke
                    # if the platform has group number like 'GKE_3',
                    # just remove the '_3'
                    neat_platform = cls.get_neat_platform(platform)
                    job_name = job['name'] + '_' + neat_platform
                    job['name'] = job_name
                    _all_jobs_in_one_platform.append(job_name)
                    if 'environment' in job:
                        if cls.deploy_type == cls._on_premise_type:
                            job['environment']['PARENT_INSTALL_JOB'] = _common_job_names['install']
                        else:
                            job['environment']['PARENT_INSTALL_JOB'] = _common_job_names['dhaas_creation']
                        if 'JOB_NAME' in job['environment']:
                            job['environment']['JOB_NAME'] = job['name']
                    if 'deployments' in job and len(job['deployments']) > 0 and 'repository' in job['deployments'][0]:
                        job['deployments'][0]['repository'] += '_' + neat_platform

            # init basic_depends_on in one platform
            if cls.deploy_type == cls._on_premise_type:
                _basic_depends_on = [{'job': _common_job_names['k8s_creation'],
                                      'on': ['finished']},
                                     {'job': _common_job_names['install'],
                                      'on': ['finished']}]
            else:
                _basic_depends_on = [{'job': _common_job_names['dhaas_creation'],
                                      'on': ['finished']}]
            # all test jobs + basic depends on
            _test_depends_on = _basic_depends_on[:]
            for job_name in _all_jobs_in_one_platform:
                dep_job = {'job': '', 'on': ['*']}
                dep_job['job'] = job_name
                _test_depends_on.append(dep_job)

            # init all depends on for test jobs.
            # Include k8s_creation& install only
            for job in merged_jobs[platform]:
                neat_platform = cls.get_neat_platform(platform)
                if job['name'].startswith('k8s_creation'):
                    job['environment']['USE_FOR'] = cls._use_for
                    _, job['environment']['PROVISION_PLATFORM'] = cls.get_platform(platform)

                if job['name'].startswith('dhaas_creation'):
                    job['environment']['USE_FOR'] = cls._use_for
                    _, job['environment']['PROVISION_PLATFORM'] = cls.get_platform(platform)
                    job['environment']['VORA_VERSION'] = cls.releasepack_version
                    job['environment']['GERRIT_CHANGE_BRANCH'] = cls.codeline

                if job['name'].startswith('install_'):
                    job['depends_on'] = []
                    job['depends_on'].append(_basic_depends_on[0])
                    job['environment']['K8S_CREATION_JOB'] = _common_job_names['k8s_creation']
                    _, job['environment']['PROVISION_PLATFORM'] = cls.get_platform(platform)
                    job['environment']['USE_FOR'] = cls._use_for
                    job['environment']['VORA_VERSION'] = cls.releasepack_version
                    job['environment']['GERRIT_CHANGE_BRANCH'] = cls.codeline

                if job['name'].endswith('test_' + neat_platform):
                    job['depends_on'] = _basic_depends_on[:]

                if job['name'].startswith('log_collection'):
                    job['depends_on'] = deepcopy(_test_depends_on)
                    if cls.deploy_type == cls._on_premise_type:
                        job['environment']['PARENT_INSTALL_JOB'] = _common_job_names['install']
                    else:
                        job['environment']['PARENT_INSTALL_JOB'] = _common_job_names['dhaas_creation']

                if job['name'].startswith('uninstall_'):
                    job['depends_on'] = deepcopy(_test_depends_on)
                    append_list = [_common_job_names['log_collection']]
                    append_common_jobs(cls, append_list, 'finished')
                    refresh_depends_on_status(cls, job['depends_on'],
                                              platform,
                                              'finished')
                    job['environment']['K8S_CREATION_JOB'] = _common_job_names['k8s_creation']
                    job['environment']['USE_FOR'] = cls._use_for
                    _, job['environment']['PROVISION_PLATFORM'] = cls.get_platform(platform)
                    job['environment']['VORA_VERSION'] = cls.releasepack_version

                if job['name'].startswith('k8s_deletion'):
                    job['depends_on'] = deepcopy(_test_depends_on)
                    append_list = [_common_job_names['log_collection'],
                                   _common_job_names['uninstall']]
                    append_common_jobs(cls, append_list, 'finished')
                    refresh_depends_on_status(cls, job['depends_on'],
                                              platform,
                                              'finished')
                    job['environment']['K8S_CREATION_JOB'] = _common_job_names['k8s_creation']
                    job['environment']['USE_FOR'] = cls._use_for
                    _, job['environment']['PROVISION_PLATFORM'] = cls.get_platform(platform)

                if job['name'].startswith('dhaas_deletion'):
                    job['depends_on'] = deepcopy(_test_depends_on)
                    append_list = [_common_job_names['log_collection']]
                    append_common_jobs(cls, append_list, 'finished')
                    refresh_depends_on_status(cls, job['depends_on'],
                                              platform,
                                              'finished')
                    job['environment']['USE_FOR'] = cls._use_for

                if job['name'].startswith('job_report'):
                    job['depends_on'] = deepcopy(_test_depends_on)
                    for index in range(len(job['depends_on'])):
                        job['depends_on'][index]['on'] = ['*']
                    if cls.deploy_type == cls._on_premise_type:
                        append_list = [_common_job_names['log_collection'],
                                       _common_job_names['uninstall'],
                                       _common_job_names['k8s_deletion']]
                        job['environment']['PARENT_INSTALL_JOB'] = _common_job_names['install'] 
                    else:
                        append_list = [_common_job_names['log_collection'],
                                       _common_job_names['dhaas_deletion']]
                        job['environment']['PARENT_INSTALL_JOB'] = _common_job_names['dhaas_creation']
                    append_common_jobs(cls, append_list, '*')
                    job['environment']['FULL_PLATFORM'] = cls._full_platform
                    job['environment']['DEPLOY_TYPE'] = cls.deploy_type
                    job['environment']['USE_FOR'] = cls._use_for
                    job['environment']['GERRIT_CHANGE_BRANCH'] = cls.codeline
                    job['environment']['VORA_VERSION'] = cls.releasepack_version

        update_dependency_matrix_platform(cls, dependency_matrix, testplans)
        # add the dependency by the defination of csv files
        refresh_depends_by_csv(cls, merged_jobs, dependency_matrix, testplans)
        return merged_jobs

    @classmethod
    def combine_job_report(cls, combine_platform, merged_jobs):
        """
        return the job_report for multi groups
        and also remove the job_report job from multi group
        """
        _job_report = {}
        for platform in merged_jobs:
            if 'DHAAS_AWS' not in platform:
                name = platform.split('_')
            else:
                name = [platform[:platform.rfind('_')], platform[platform.rfind('_')+1:]]
            if len(name) > 1 and name[0] == combine_platform:
                for job in merged_jobs[platform]:
                    if job['name'].startswith('job_report'):
                        if not _job_report:
                            _job_report = deepcopy(job)
                        else:
                            _job_report['depends_on'] += job['depends_on']
                        # remove the job_report from _common_jobs for multi group
                        merged_jobs[platform].pop(merged_jobs[platform].index(job))
        return _job_report

    @classmethod
    def filter_jobs_and_update_env_by_testplans(cls, merged_jobs, testplans):
        '''
        Remove the jobs from infrabox_json that not defined in testplans
        format of testplans:
            {
                "GKE_1": {
                "vora_tools_ui_e2e_test": {
                    "SUITE": "vora"
                    }
                ...
                }
                "GKE_2": { 
                    ...
                }
            }
        '''
        # replace the AWS-EKS to EKS, replace the AZURE-AKS to AKS
        # job_names_in_platform = {'platform': ['job_name1', 'job_name2'...]}
        job_names_in_platform = {}
        for platform in testplans:
            # platform_short = cls.convert_platform(platform)
            if platform not in job_names_in_platform:
                job_names_in_platform[platform] = []
            job_names_in_platform[platform] = list(testplans[platform].keys())

        for platform in merged_jobs:
            keep_jobs_in_current_platform = []
            neat_platform = cls.get_neat_platform(platform)
            for index in range(len(merged_jobs[platform])):
                job_name = merged_jobs[platform][index]['name']
                # only common jobs like install_1gke, job_report_gke has suffix '_platform'
                platform_full = cls.convert_platform(platform, False)
                if job_name in job_names_in_platform[platform_full] or job_name.endswith(neat_platform) is True:
                    # over wirte the 'enviroments'
                    if job_name in testplans[platform_full] and len(testplans[platform_full][job_name]) > 0:
                        if 'environment' not in merged_jobs[platform][index]:
                            merged_jobs[platform][index]['environment'] = {}
                        merged_jobs[platform][index]['environment'].update(testplans[platform_full][job_name])

                    keep_jobs_in_current_platform.append(merged_jobs[platform][index])
            if len(keep_jobs_in_current_platform) > 0:
                merged_jobs[platform] = keep_jobs_in_current_platform

    @classmethod
    def combine_common_and_jobs(cls, testplans, testjobs, common_jobs, dependency_matrix):
        """
        combine the jobs and common templetes
        """
        infrabox_json = {
            'version': 1,
            'jobs': []
        }
        merged_jobs = cls.insert_validation_jobs_into_common_tem(testjobs,
                                                                 common_jobs)
        cls.update_common_job_names(merged_jobs)
        # till now all the jobs has been insert into common templete,
        # the {_platform} and {group}{_platform} has been update for command job names
        # the {_platform}  has been update for all jobs
        # also the depends on in normal test jobs are missing.
        # also the there are multi job_report_platform jobs in multi group

        # update the depends on and remove the jobs not defined in TestPlans.json
        # also update the env by the defination in TestPlans.json
        cls.update_depends_and_job_names(merged_jobs,
                                         dependency_matrix,
                                         testplans)
        # till now all the jobs has propere depends_on
        # (k8s_creation_<group><platform>, install_<group><platform>)

        # combine multi job_report_platform jobs for multi group
        job_report_dic = {}
        for platform in cls.group_number:
            job_report = cls.combine_job_report(platform, merged_jobs)
            if job_report:
                job_report_dic[platform] = job_report

        for platform in merged_jobs:
            for job in merged_jobs[platform]:
                infrabox_json['jobs'].append(job)
        for platform, job in job_report_dic.items():
            infrabox_json['jobs'].append(job)

        # till now, the infrabox_json contains full jobs
        # missing part: validtion jobs depends_on in non-common jobs
        return infrabox_json

    @classmethod
    def parse_dependency(cls, df):
        """
        input: csv is the file operator
        """
        # jobs_with_dep = {'job1': ['dep_job1', 'dep_job2'], 'job2':[]}
        jobs_with_dep = {}
        jobs_left_col = []
        for i in range(df.columns.size):
            jobs_current_col = []
            col_name = 'col' + str(i + 1)
            column = df[col_name]
            for row in range(column.size):
                if col_name == 'col1':
                    if column[row] is not np.nan:
                        jobs_with_dep[column[row]] = []
                        jobs_current_col.append(column[row])
                else:
                    if column[row] is not np.nan:
                        jobs_with_dep[column[row]] = jobs_left_col
                        jobs_current_col.append(column[row])
            jobs_left_col = jobs_current_col
        return jobs_with_dep

    @classmethod
    def read_dependency(cls):
        """
        load the dependency *.csv file from
        database/temp_details/gke/dependency/*.csv
        """
        dependency_matrix = {}
        for platform in cls.group_number:
            if cls.group_number[platform] > 0:
                for i in range(cls.group_number[platform]):
                    dep_file = os.path.join(cls._template_detail_folder, platform.lower(), 'dependency', 'dependency_' + str(i+1) + '.csv')
                    if os.path.exists(dep_file) is False:
                        continue
                    df = pd.read_csv(dep_file)
                    jobs_with_dep = cls.parse_dependency(df)
                    dependency_matrix[platform + '_' + str(i+1)] = jobs_with_dep
            else:
                dep_file = os.path.join(cls._template_detail_folder,
                                        platform.lower(),
                                        'dependency',
                                        'dependency.csv')
                if os.path.exists(dep_file) is False:
                    continue
                df = pd.read_csv(dep_file)
                jobs_with_dep = cls.parse_dependency(df)
                dependency_matrix[platform] = jobs_with_dep
        return dependency_matrix

    @classmethod
    def init(cls):
        cls.deploy_type = str(os.environ.get("DEPLOY_TYPE", cls._on_premise_type))
        if cls.deploy_type == cls._on_premise_type:
            cls.group_number = {
                'AKS': 0,
                'EKS': 0,
                'GKE': 0,
                'MONSOON': 0
            }
        elif cls.deploy_type == cls._on_cloud_type:
            cls.group_number = {'DHAAS_AWS': 0}
        else:
            raise ValueError('Request deploy_type missing. It should be on_premise or on_cloud')
        cls.codeline = str(os.environ.get("CODELINE", "stable"))
        cls.releasepack_version = str(os.environ.get("RELEASEPACK_VERSION", ''))
        cls.releasepack_refs = os.environ.get("RELEASEPACK_REFS", None)
        if not cls.releasepack_version:
            raise ValueError('RELEASEPACK_VERSION is missing')

    @classmethod
    def get_full_platform_by_testplans(cls, testplans):
        """
        get full platform from testplan
        """
        full_platform = []
        for platform in testplans:
            name = cls.get_neat_platform(platform)
            f_on_pre = lambda name: name.split('-')[1] if 'dhaas' not in name and '-' in name else name
            f_on_cloud = lambda name: name.replace('-','_') if 'dhaas' in name else name
            name = f_on_cloud(f_on_pre(name))
            if name not in full_platform:
                full_platform.append(name)
        return ','.join(full_platform)

    @classmethod
    def main(cls, env=None):
        """
        Clone `hanalite-releasepack`
        """
        cls.init()
        repo = 'ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack'
        # only clone depth 1 and only one branch, reagarding to the
        cls.clone(repo, os.path.join(cls.current_path, 'hanalite-releasepack'))
        testplans = cls.read_test_plans()
        cls._full_platform = cls.get_full_platform_by_testplans(testplans)
        
        # Read the test job template from "database/temp_details"
        testjobs, common_jobs = cls.read_test_job_templete()
        # remove the platform that not used in TestPlans.json
        common_jobs = {platform:v for platform, v in common_jobs.items() if platform.lower() in cls._full_platform.split(',')}
        # tricky: the platform AWS-EKS in job name is EKS, but it's AWS-EKS in testplans.json
        # rename the AWS-EKS to EKS in group_number dic
        if 'AWS-EKS' in cls.group_number:
            cls.group_number['EKS'] = cls.group_number.pop('AWS-EKS')
        # handle depends_on releationship
        # read the *.csv file for dependency
        # dependency_matrix = {platform: {'job1': [], 'job2':['jobx']}, platform: {}}
        dependency_matrix = cls.read_dependency()
        # combine testjobs and common_jobs into one single infrabox.json
        infrabox_json = cls.combine_common_and_jobs(testplans,
                                                    testjobs,
                                                    common_jobs,
                                                    dependency_matrix)

        # add "build_context": "/data/repo/bdh-infra-tools" for each job
        # and "repository": { "full_history": true } for each job
        for index in range(len(infrabox_json['jobs'])):
            infrabox_json['jobs'][index]['build_context'] = '/data/repo/bdh-infra-tools'
            if 'repository' not in infrabox_json['jobs'][index]:
                infrabox_json['jobs'][index]['repository'] = { 'full_history': True }

        with open('/infrabox/output/origin.json', 'w') as txt:
            json.dump(infrabox_json, txt)
        shutil.copyfile('/infrabox/output/origin.json',
                        '/infrabox/upload/archive/origin.json')

if __name__ == '__main__':
    try:
        AssembleInfraboxJson.main()
    except Exception as inst:
        logger.error("### [level=error] failure during infrabox.json assembling. Exception:%s. %s" %
                     (str(type(inst)), str(inst.args)))
        raise
