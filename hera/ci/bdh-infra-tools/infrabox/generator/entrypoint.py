#!/usr/bin/env python

import sys
import json
import logging
import copy

def get_feature_toggle_settings(git_log_file):
    feature_toggles = ''
    feature_toggles_list = []
    with open(git_log_file) as f:
        lines = f.readlines()
        for l in lines:
            if l.lower().startswith('feature toggles:'):
                feature_toggles = l[len('feature toggles:'):]
                break
    return feature_toggles

def add_feature_toggle_validation(infrabox_json, feature_toggles):
    prepare_jobs = ['build', 'mirror_docker_image']
    add_jobs = copy.deepcopy(infrabox_json['jobs'])
    add_jobs = [job for job in add_jobs if not (job['name'] in prepare_jobs or job['name'].startswith('job_report'))]
    for job in add_jobs:
        job['name'] = 'ff_val_' + job['name']
        if 'dhaas_creation' in job['name'] or 'install' in job['name']:
            ff_job = None
            with open('/project/feature_toggle_job_temp.json', 'r') as f:
                ff_job = json.load(f)
            ff_job_name = 'handle_feature_toggle'
            if 'dhaas_creation' in job['name']:
                ff_job_name = ff_job_name + job['name'][len('ff_val_dhaas_creation'):]
            else:
                ff_job_name = ff_job_name + job['name'][len('ff_val_install'):]
            ff_job['name'] = ff_job_name
            ff_job['environment']['PARENT_INSTALL_JOB'] = job['name'][len('ff_val_'):]
            ff_job['environment']['FEATURE_TOGGLES'] = feature_toggles
            ff_job['environment']['DISABLE_REGISTER_FF'] = 'true'
            ff_job['depends_on'][0]['job'] = job['name'][len('ff_val_'):]
            add_jobs.append(copy.deepcopy(ff_job))
        if 'depends_on' in job:
            for depend in job['depends_on']:
                if depend['job'] not in prepare_jobs:
                    depend['job'] = 'ff_val_' + depend['job']
            if 'test' in job['name']:
                ff_job_name = 'ff_val_handle_feature_toggle' + job['name'].split('test')[1]
                job['depends_on'].append({'job':ff_job_name, 'on':['finished']})
        if 'environment' in job:
            if 'PARENT_INSTALL_JOB' in job['environment']:
                job['environment']['PARENT_INSTALL_JOB'] = 'ff_val_' + job['environment']['PARENT_INSTALL_JOB']
            if 'K8S_CREATION_JOB' in job['environment']:
                job['environment']['K8S_CREATION_JOB'] = 'ff_val_' + job['environment']['K8S_CREATION_JOB']
    infrabox_json['jobs'] += add_jobs
    return infrabox_json

if __name__ == "__main__":
    git_log_path = sys.argv[1]
    infrabox_json_file = sys.argv[2]

    with open(infrabox_json_file,'r') as load_f:
      infrabox_json = json.load(load_f)
      print(infrabox_json)

    feature_toggles = get_feature_toggle_settings(git_log_path)
    if feature_toggles:
        infrabox_json = add_feature_toggle_validation(infrabox_json, feature_toggles)

    with open('/project/infrabox_adapt.json', 'w') as f:
        json.dump(infrabox_json, f)

