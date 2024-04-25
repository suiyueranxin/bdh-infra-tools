import os
import sys
import json
import logging
import shutil
from assemble import AssembleInfraboxJson
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

class UpgradeGenerator(object):
    def __init__(self):
        self.needed_env = ["VORA_VERSION", "BASE_BDH_VERSIONS", "VORA_KUBE_PREFIX_URL", "GERRIT_CHANGE_BRANCH", "GERRIT_CHANGE_PROJECT", "PACKAGE_PATTERN", "DEPLOY_TYPE"]
        self.base_bdh_versions = []
        self.full_platform = []
        self.upgrade_with_di = False
        self.current_path = os.path.dirname(os.path.realpath(__file__))
        AssembleInfraboxJson.set_use_for('MILESTONE_VALIDATION_upgrade')
        AssembleInfraboxJson.cycle_name = {
            "on_cloud": "MILESTONE_VALIDATION_upgrade_on_cloud",
            "on_premise": "MILESTONE_VALIDATION_upgrade_on_premise"
        }
        AssembleInfraboxJson.platform_folder = {
            'AKS': 'aks',
            'EKS': 'eks',
            'GKE': 'gke',
            'DHAAS-AWS': 'dhaas_aws'
        }

    def _check_env_available(self):
        return True if all(env in os.environ for env in self.needed_env) else False

    def generate_upgrade_jobs(self, job_template, parent_install_job, versions):
        """
        " Generate upgrade jobs with job template, base_bdh_versions
        " Inputs: 
        "      job: upgrade job template
        "      install_job: parent install job
        "      versions: generated jobs with different versions
        " Output:
        "      A list of system_upgrade jobs
        """
        upgrade_jobs = []
        if "name" not in job_template or "environment" not in job_template:
            logger.warning("Invalid template, please check")
            return upgrade_jobs
        if "depends_on" not in job_template:
            job_template["depends_on"] = []
        for index in range(len(versions)):
            job = deepcopy(job_template)
            job["name"] = job["name"].replace("<INDEX>", str(index + 1))
            job["environment"]["VORA_VERSION"] = versions[index]
            job['environment']['PARENT_INSTALL_JOB'] = parent_install_job
            if self.upgrade_with_di:
                job["environment"]["VORA_KUBE_SUFFIX"] = "DI-Assembly"
            if index >= 1:
                #From second job, need to depends on it's parent system upgrade job
                depend = {"job": job_template["name"].replace("<INDEX>", str(index)), "on": ["finished"]}
                job["depends_on"].append(depend)
            upgrade_jobs.append(job)
            parent_install_job = job["name"]
        return upgrade_jobs

    def seperate_depends(self, dependency_matrix):
        prepare_depends = {}
        validation_depends = {}
        for platform in dependency_matrix:
            prepare_depends[platform] = {}
            validation_depends[platform] = {}
            for job in dependency_matrix[platform]:
                if 'preparation' in job:
                    prepare_depends[platform][job] = dependency_matrix[platform][job]
                else:
                    validation_depends[platform][job] = dependency_matrix[platform][job]
                    for depended_job in validation_depends[platform][job]:
                        if 'preparation' in depended_job:
                            validation_depends[platform][job].remove(depended_job)   
                        
        return {'preparation': prepare_depends, 'validation': validation_depends}

    def seperate_test_plans(self, test_plans):
        prepare_test_plan = {}
        validation_test_plan ={}
        for platform in test_plans:
            cur_platform = 'DHAAS_AWS' if platform == 'DHAAS-AWS' else platform
            prepare_test_plan[cur_platform] = {}
            validation_test_plan[cur_platform] = {}
            for job in test_plans[platform]:
                if 'preparation' in job:
                    prepare_test_plan[cur_platform][job] = test_plans[platform][job]
                else:
                    validation_test_plan[cur_platform][job] = test_plans[platform][job]                  
        return {'preparation': prepare_test_plan, 'validation': validation_test_plan}

    def assmble_single_job(self, testjobs, job_name, job_env):
        new_job = None
        #job_env is from test_plan
        for job in testjobs:
            if job['name'] == job_name:
                new_job = deepcopy(job)
                if 'environment' in new_job and job_env is not None:
                    #combin 'environment' from new_job and job_env, if duplicated, use env in jobs_env
                    new_job['environment'] = dict(job_env, **new_job['environment'])
                elif 'environment' not in new_job and job_env is not None:
                    new_job['environment'] = deepcopy(job_env)
                elif 'environment' not in new_job and job_env is None:
                    new_job['environment'] = {}
        return new_job


    def assmble_test_jobs(self, test_plans, testjobs):
        assmbled_jobs ={}
        for test_type in test_plans:
            assmbled_jobs[test_type] = {}
            for platform in test_plans[test_type]:
                assmbled_platform = 'EKS' if platform == 'AWS-EKS' else platform
                assmbled_jobs[test_type][assmbled_platform] = []
                for job in test_plans[test_type][platform]:
                    new_job = self.assmble_single_job(testjobs, job, test_plans[test_type][platform][job])
                    if new_job is not None:
                        assmbled_jobs[test_type][assmbled_platform].append(new_job)
        return assmbled_jobs

    def combin_job_templates(self, common_jobs, test_plans, testjobs):
        test_jobs = self.assmble_test_jobs(test_plans, testjobs)
        _common_jobs = deepcopy(common_jobs)
        for platform, common_jobs_in_platform in _common_jobs.items():
            # c_job: iterate in common template
            for c_job in common_jobs_in_platform:
                if c_job['name'].startswith(('k8s_creation', 'dhaas_creation_')):
                    #preparation jobs were inserted after k8s_creation or dhaas_creation
                    install_job_index = common_jobs_in_platform.index(c_job)
                    common_jobs_in_platform[install_job_index + 1:
                                            install_job_index + 1] = deepcopy(test_jobs['preparation'][platform])
                    break
            for c_job in common_jobs_in_platform:
                if c_job['name'].startswith(('system_upgrade')):
                    # valdiation test jobs were inserted after system_upgrade
                    upgrade_job_index = common_jobs_in_platform.index(c_job)
                    common_jobs_in_platform[upgrade_job_index + 1:
                                            upgrade_job_index + 1] = deepcopy(test_jobs['validation'][platform])
                    break
        return _common_jobs

    def upgrade_job_name_with_platform(self, merged_jobs):
        for platform, jobs in merged_jobs.items():
            if jobs is not None:
                for job in jobs:
                    if 'name' in job and platform.lower()  not in job['name']:
                        if job['name'] == 'fetch-e2e-secrets':
                            continue
                        else:
                            job['name'] = job['name'] + '_' + platform.lower()
        return merged_jobs

    def get_k8s_creation_job(self, joblist):
        if len(joblist) == 0:
            return None
        for job in joblist:
            if 'name' in job and 'k8s_creation' in job['name'] or 'dhaas_creation' in job['name']:
                return job['name']
        return None

    def get_last_upgrade_job(self, joblist, base_versions):
        if len(joblist) == 0:
            return None
        name_pattern = 'system_upgrade_' + str(len(base_versions))
        for job in joblist:
            if 'name' in job and name_pattern in job['name']:
                return job['name']
        return None

    def insert_upgrade_jobs(self, jobs, base_versions):
        parent_install_job = self.get_k8s_creation_job(jobs)
        upgrade_job_pos = -1
        for pos in range(len(jobs)):
            if 'name' in jobs[pos] and 'system_upgrade' in jobs[pos]['name']:
                upgrade_job_pos = pos
                break
        if upgrade_job_pos < 0:
            logger.warning("No system upgrade job found in template, please check job template")
            return None 
        upgrade_job = deepcopy(jobs[upgrade_job_pos])
        target_jobs = []   
        if "depends_on" not in upgrade_job:
            upgrade_job["depends_on"] = []          
        if len(base_versions) >= 2:
            #If there are 2 or more base bdh versions, it's need to generate system upgrade jobs with different base versions
            target_jobs = self.generate_upgrade_jobs(upgrade_job, parent_install_job, base_versions[1:])
            parent_install_job = upgrade_job["name"].replace("<INDEX>", str(len(base_versions) - 1))
            upgrade_job["depends_on"].append({"job": parent_install_job, "on": ["finished"]})   
            #upgrade to target version
        upgrade_job["name"] = upgrade_job["name"].replace("<INDEX>", str(len(base_versions)))
        if 'environment' not in upgrade_job:
            upgrade_job['environment'] = {}
        upgrade_job['environment']['PARENT_INSTALL_JOB'] = parent_install_job
        upgrade_job['environment']['VORA_VERSION'] = os.environ.get('VORA_VERSION')
        if self.upgrade_with_di:
            upgrade_job["environment"]["VORA_KUBE_SUFFIX"] = "DI-Assembly"
        jobs[upgrade_job_pos] = upgrade_job
        return jobs[:upgrade_job_pos] + target_jobs + jobs[upgrade_job_pos:]


    def update_depends_with_plt(self, dependency_matrix):
        cur_depends ={'preparation':{},'validation':{}}
        for test_type in dependency_matrix:
            for platform in dependency_matrix[test_type]:
                cur_depends[test_type][platform] = {}
                for job, depends in dependency_matrix[test_type][platform].items():
                    if 'name' in job and platform.lower()  not in job['name']:
                        job['name'] = job['name'] + '_' + platform.lower()
                    cur_depends[test_type][platform][job] = []
                    for depend in depends:
                        if 'name' in depend and platform.lower()  not in depend['name']:
                            depend['name'] = depend['name'] + '_' + platform.lower()
                        cur_depends[test_type][platform][job].append(depend)                      
        return cur_depends

    def update_env(self, platform, jobs, base_versions):
        vora_version = os.environ.get('VORA_VERSION')
        k8s_creation_job = self.get_k8s_creation_job(jobs)
        last_upgrade_job = self.get_last_upgrade_job(jobs, base_versions)   
        #full_platform =  AssembleInfraboxJson._full_platform.split(',')
        #full_platform = full_platform* len(self.base_bdh_versions)
        for job in jobs:
            if "environment" not in job:
                job["environment"] = {}  
            job["environment"]["GERRIT_CHANGE_BRANCH"] = os.environ['GERRIT_CHANGE_BRANCH']
            job["environment"]["GERRIT_CHANGE_PROJECT"] = os.environ["GERRIT_CHANGE_PROJECT"]
            job["environment"]["VORA_KUBE_PREFIX_URL"] = os.environ["VORA_KUBE_PREFIX_URL"]
            job["build_context"] = "/data/repo" 
            if "system_upgrade" not in job['name']:
                job["environment"]["VORA_VERSION"] =  vora_version
            if 'creation' in job['name']:
                job["environment"]["BASE_BDH_VERSION"] = base_versions[0]
                if self.upgrade_with_di:
                    job["environment"]["VORA_KUBE_SUFFIX"] = "DI-Assembly" 
                continue
            job["environment"]["K8S_CREATION_JOB"] = k8s_creation_job
            if 'preparation' in job['name']:
                job["environment"]["PARENT_INSTALL_JOB"] = k8s_creation_job
                job["environment"]["ENV_FILE"] = "/infrabox/inputs/" + k8s_creation_job + "/env.sh"
            if 'test' in job['name'] and 'preparation' not in job['name'] and \
                'system_upgrade' not in job['name']:
                job["environment"]["PARENT_INSTALL_JOB"] = last_upgrade_job
                job["environment"]["ENV_FILE"] = "/infrabox/inputs/" + last_upgrade_job + "/env.sh" 
            if 'log_collection' in job['name']:
                job["environment"]["PARENT_INSTALL_JOB"] = last_upgrade_job
            if 'job_report' in job['name']:
                job["environment"]["FULL_PLATFORM"] = ','.join(self.full_platform)
                job["environment"]["BASE_BDH_VERSIONS"] = ','.join(base_versions)                     
                job["environment"]["PARENT_INSTALL_JOB"] = last_upgrade_job
        return jobs

    def get_base_bdh_versions(self):
        if not self._check_env_available():
            logger.warning("env is invalid")
            return []
        base_versions = os.environ["BASE_BDH_VERSIONS"]
        if '[' in base_versions:
            base_versions = base_versions.split('[')[1]
        if ']' in base_versions:
            base_versions = base_versions.split(']')[0]
        base_versions = base_versions.split(',')
        self.base_bdh_versions = deepcopy(base_versions)
        return self.base_bdh_versions

    def get_jobs_name_list(self, jobs):
        name_list = []
        for job in jobs:
            if 'name' in job:
                name_list.append(job['name'])
        return name_list

    def get_test_jobs(self, jobs, platform, test_plans, test_job_type='validation'):
        platform_in_testplan = 'AWS-EKS' if platform == 'EKS' else platform
        all_jobs = self.get_jobs_name_list(jobs)
        test_jobs = []
        if test_job_type not in ['preparation', 'validation']:
            return []
        if platform_in_testplan in test_plans[test_job_type]:
            for job in test_plans[test_job_type][platform_in_testplan].keys():
                job_name = job + '_' + platform.lower()
                if job_name in all_jobs:
                    test_jobs.append(job_name)
        return test_jobs

    def update_test_jobs_depends(self, jobs, platform, test_plans, dependency_matrix, base_versions):
        last_upgrade_job = self.get_last_upgrade_job(jobs, base_versions)
        preparation_jobs = self.get_test_jobs(jobs, platform, test_plans, 'preparation')
        validation_jobs = self.get_test_jobs(jobs, platform, test_plans)
        preparation_depends = dependency_matrix['preparation'][platform]
        validatoin_depends = dependency_matrix['validation'][platform]
        for job in jobs:
            if job['name'] in preparation_jobs or job['name'] in validation_jobs:
                if "depends_on" not in job:
                    job["depends_on"] = []
            if job['name'] in preparation_jobs and job['name'] in preparation_depends:
                #Add depends for preparation jobs 
                #1. add depends from dependency_matrix for preparation jobs 
                depend_jobs = preparation_depends[job['name']]
                for depend_job in depend_jobs:
                    job["depends_on"].append({"job": depend_job, "on": ["*"]})
            if job['name'] in validation_jobs:
                # Add depends for validation jobs
                if job['name'] in validatoin_depends:
                    #1. add depends from dependency_matrix for validation jobs 
                    depend_jobs = validatoin_depends[job['name']]
                    for depend_job in depend_jobs:
                        job["depends_on"].append({"job": depend_job, "on": ["*"]})    
                if 'validation' in job['name']: 
                    depend_prepare_job_name = job['name'].replace('validation', 'preparation')
                    #2. find preparation jobs that validation jobs depends on 
                    if depend_prepare_job_name in preparation_jobs:
                        job["depends_on"].append({"job": depend_prepare_job_name, "on": ["finished", "unstable"]})
                #3. All validation jobs will depends on last upgrade job
                job["depends_on"].append({"job": last_upgrade_job, "on": ["finished", "unstable"]})
                job["environment"]["BASE_BDH_VERSION"] = base_versions[0]
            if "default_tenant" in job.get("name"):
                job.get("depends_on").append({"job": "fetch-e2e-secrets",
                        "on": [
                            "*"
                        ]})   
        return jobs


    def update_depends(self, platform, jobs, dependency_matrix, base_versions, test_plans):
        k8s_creation_job = self.get_k8s_creation_job(jobs)
        last_upgrade_job = self.get_last_upgrade_job(jobs, base_versions)
        preparation_jobs = self.get_test_jobs(jobs, platform, test_plans, 'preparation')
        validation_jobs = self.get_test_jobs(jobs, platform, test_plans)
        jobs = deepcopy(self.update_test_jobs_depends(jobs, platform, test_plans, dependency_matrix, base_versions))
        for index in range(1, len(jobs)):
            if "depends_on" not in jobs[index]:
                jobs[index]["depends_on"] = []
            job_name = jobs[index]['name']
            if job_name.startswith('log_collection') or job_name.startswith('job_report'):
                for pre_job in jobs[: index]:
                    jobs[index]["depends_on"].append({"job": pre_job["name"], "on": ["*"]})
            else:
                jobs[index]["depends_on"].append({"job": k8s_creation_job, "on": ["finished"]})
                if job_name.startswith('system_upgrade_1'):
                    for prepara_job in preparation_jobs:
                        jobs[index]["depends_on"].append({"job": prepara_job, "on": ["*"]})
                    
                if job_name.startswith('k8s_upgrade') or '_deletion_' in job_name:
                    jobs[index]["depends_on"].append({"job": last_upgrade_job, "on": ["finished"]})
                    condition = '*'
                    if '_deletion_' in job_name:
                        jobs[index]["depends_on"].append({"job": jobs[index - 1]['name'], "on": ["*"]})
                        condition = 'finished'
                    for validation_job in validation_jobs:
                        jobs[index]["depends_on"].append({"job": validation_job, "on": [condition]})
        return jobs

    def generate_with_base_versions(self, merged_jobs, base_versions, dependency_matrix, test_plans):
        _merged_jobs = deepcopy(merged_jobs)
        _merged_jobs = self.upgrade_job_name_with_platform(_merged_jobs)
        current_dependency = deepcopy(dependency_matrix)
        current_dependency = self.update_depends_with_plt(current_dependency)
        for platform, jobs in _merged_jobs.items():        
            #insert mulitple steps upgrade jobs   
            inserted_jobs = self.insert_upgrade_jobs(jobs, base_versions)
            if inserted_jobs is not None:
                _merged_jobs[platform] = inserted_jobs
                jobs = deepcopy(inserted_jobs) 
            #update depends for every jobs    
            updated_depends_jobs = self.update_depends(platform, jobs, current_dependency, base_versions, test_plans)
            if updated_depends_jobs is not None:
                _merged_jobs[platform] = updated_depends_jobs
                jobs = deepcopy(updated_depends_jobs) 
            #update env for every jobs
            updated_env_jobs = self.update_env(platform, jobs, base_versions)
            if updated_env_jobs is not None:
                _merged_jobs[platform] = updated_env_jobs
                jobs = deepcopy(updated_env_jobs) 
        return _merged_jobs

    def skip_run_on_platform(self, dependency_matrix, common_jobs, testplans, platform):
        if platform in dependency_matrix['preparation']:
            del dependency_matrix['preparation'][platform]
        if platform in dependency_matrix['validation']:
            del dependency_matrix['validation'][platform]
        if platform in common_jobs:
            del common_jobs[platform]
        if platform in testplans:
            del testplans[platform]
        self.full_platform.remove(platform.lower())                    

    def main(self):
        if not self._check_env_available():
            logger.warning("env is invalid")
            sys.exit(1)
        os.environ['RELEASEPACK_VERSION'] = os.environ.get('VORA_VERSION')   
        os.environ['CODELINE'] = 'master' if os.environ.get('GERRIT_CHANGE_BRANCH') == 'main' else os.environ.get('GERRIT_CHANGE_BRANCH')
        AssembleInfraboxJson.init()
        repo = 'ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack'
        # only clone depth 1 and only one branch, reagarding to the
        AssembleInfraboxJson.clone(repo, os.path.join(self.current_path, 'hanalite-releasepack'))
        testplans = AssembleInfraboxJson.read_test_plans()
        AssembleInfraboxJson.set_full_platform(AssembleInfraboxJson.get_full_platform_by_testplans(testplans))
        testjobs, common_jobs = AssembleInfraboxJson.read_test_job_templete()
        common_jobs = {platform:v for platform, v in common_jobs.items() if platform.lower() in AssembleInfraboxJson.get_full_platform().split(',')}
        # tricky: the platform AWS-EKS in job name is EKS, but it's AWS-EKS in testplans.json
        # rename the AWS-EKS to EKS in group_number dic
        if 'AWS-EKS' in AssembleInfraboxJson.group_number:
            AssembleInfraboxJson.group_number['EKS'] = AssembleInfraboxJson.group_number.pop('AWS-EKS')
        if "DI-Assembly" in os.environ.get("PACKAGE_PATTERN", "Foundation"):
            self.upgrade_with_di = True
        self.get_base_bdh_versions()
        #dependency will be seperate to 2 parts: 1, preparetion test 2, validation test
        dependency_matrix = self.seperate_depends(AssembleInfraboxJson.read_dependency())
        self.full_platform = AssembleInfraboxJson.get_full_platform().split(',')
        # tricky, upgrade will not run on AKS, if the base version is 2.7.* and in rel-3.0, base version is less than 3.0.36
        if len(self.base_bdh_versions) > 0 and (self.base_bdh_versions[0].startswith('2.7.') or \
            (self.base_bdh_versions[0].startswith('3.0.')) and int(self.base_bdh_versions[0].split('.')[2]) < 36):
            self.skip_run_on_platform(dependency_matrix, common_jobs, testplans, 'AKS')        
        #test_plan will be seperate to 2 parts: 1, preparetion test 2, validation test
        test_plans = self.seperate_test_plans(testplans)
        #merge common jobs and test jobs
        merged_jobs = self.combin_job_templates(common_jobs, test_plans, testjobs)
        infrabox_json = {
            'version': 1,
            'jobs': []
        }
        
        generated_jobs = self.generate_with_base_versions(merged_jobs, self.base_bdh_versions, dependency_matrix, test_plans)  
        for jobs in generated_jobs.values():
            infrabox_json['jobs'] += jobs
 
        with open('/infrabox/output/infrabox.json', 'w') as txt:
            json.dump(infrabox_json, txt)   
        shutil.copyfile('/infrabox/output/infrabox.json',
                        '/infrabox/upload/archive/infrabox.json')   

if __name__ == '__main__':
    ug = UpgradeGenerator()
    ug.main()
