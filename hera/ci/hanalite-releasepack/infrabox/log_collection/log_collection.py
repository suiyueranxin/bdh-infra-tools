#!/usr/bin/env python

"""
Collect job logs
1. currently only collect kubernetes logs by Elasticsearch service.
2. more logs will be added with jobs
"""

import os
import json
import re
import datetime
import time
import pandas as pd
import datetime

def get_time_range(jobs):
    build_start_time = "9999-12-31 00:00:00+00:00"
    build_end_time = "0000-01-01 00:00:00+00:00"

    for job in jobs:
        job_name = job['name']
        if job_name == 'bdh-infra-tools' or job_name == 'Create Jobs' or job_name == 'parse-test-plan' or job_name == 'parse-test-metadata' or job_name == 'ci-dashboard_registration'or job_name == 'generator' or job_name=='clone_bdh-infra-tools' or job_name.startswith('job_report') or job_name.find('install')>0 or job_name.find('creation')>0 :
            continue
        job_start_date = job['start_date']
        job_end_date = job['end_date']

        if job_start_date != "None" and job_start_date < build_start_time:
            build_start_time = job_start_date
        if job_end_date != "None" and job_end_date > build_end_time:
            build_end_time = job_end_date
    
    build_start_time = re.sub(r'\.[0-9]{6}','', build_start_time)
    build_end_time = re.sub(r'\.[0-9]{6}','', build_end_time)
    return build_start_time, build_end_time

def get_split_time_ranges(build_start_time, build_end_time, time_slice_num, classified_num, slice_factor = 0):
    if classified_num == 0:
        return build_start_time, build_end_time

    start_timestamp = time.mktime(time.strptime(build_start_time.split("+")[0], '%Y-%m-%d %H:%M:%S'))
    end_timestamp = time.mktime(time.strptime(build_end_time.split("+")[0], '%Y-%m-%d %H:%M:%S'))
    duration = end_timestamp - start_timestamp
    slice = duration / time_slice_num

    if slice_factor != 0 :
        if classified_num == 1:
            slice_start_time = start_timestamp
            slice_end_time = int(start_timestamp + duration * slice_factor)
        elif classified_num == 2:
            slice_start_time = int(start_timestamp + duration * slice_factor)
            slice_end_time = end_timestamp
    else:
        slice_start_time = int(start_timestamp + slice * (classified_num - 1))
        slice_end_time = int(start_timestamp + slice * (classified_num))

    slice_start_time = datetime.datetime.fromtimestamp(slice_start_time)
    slice_end_time = datetime.datetime.fromtimestamp(slice_end_time)
    return  str(slice_start_time), str(slice_end_time)

def get_split_job_time_ranges(build_start_time, build_end_time, time_slice_num, classified_num, slice_factor = 0):
    if classified_num == 0:
        return build_start_time, build_end_time

    start_timestamp = time.mktime(time.strptime(build_start_time.split("+")[0], '%Y-%m-%d %H:%M:%S'))
    end_timestamp = time.mktime(time.strptime(build_end_time.split("+")[0], '%Y-%m-%d %H:%M:%S'))
    duration = end_timestamp - start_timestamp
    slice = duration / time_slice_num

    if slice_factor != 0 :
        if classified_num == 1:
            slice_start_time = start_timestamp
            slice_end_time = int(start_timestamp + slice*(classified_num))
        elif classified_num == 6:
            slice_start_time = int(start_timestamp + slice*(classified_num-1))
            slice_end_time = end_timestamp
        else :
            slice_start_time = int(start_timestamp + slice*(classified_num-1)) 
            slice_end_time = int(start_timestamp + slice*(classified_num))
    else:
        slice_start_time = int(start_timestamp + slice * (classified_num - 1))
        slice_end_time = int(start_timestamp + slice * (classified_num))

    slice_start_time = datetime.datetime.fromtimestamp(slice_start_time)
    slice_end_time = datetime.datetime.fromtimestamp(slice_end_time)
    return  str(slice_start_time), str(slice_end_time) 

def main():
    # get build time range and time slice
    time_slice_num = int(os.environ.get("TIME_SLICE_NUM", 2))
    classified_num = int(os.environ.get("CLASSIFIED_NUM", 0))
    with open('/infrabox/job.json', 'r') as f:   
        data = json.load(f)
    build_start_time, build_end_time = get_time_range(data['parent_jobs'])
    slice_factor = float(os.environ.get("SLICE_FACTOR", 0))
    slice_start_time, slice_end_time = get_split_job_time_ranges(build_start_time, build_end_time, time_slice_num, classified_num, slice_factor)
    job_start_time=datetime.datetime.now()
    print(job_start_time)
    print "slice_start_time = " + slice_start_time
    print "slice_end_time = " + slice_end_time

    #Fetch log from elasticsearch for fetch_times times and save *.csv to base_dir.
    fetch_times = int(os.environ.get("FETCH_TIMES", 60))
    base_dir = '/tmp/k8s_vora_log_tmp'
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    for i in range(1, fetch_times+1):
        start_time, end_time = get_split_time_ranges(slice_start_time, slice_end_time, fetch_times, i)
        start_time = re.sub(r'\.[0-9]{6}','', re.sub(' ','T', start_time))
        end_time = re.sub(r'\.[0-9]{6}','', re.sub(' ','T', end_time))
        file_name = start_time + '.csv'
        file_name = os.path.join(base_dir, file_name)
        retry_times = 0
        cmd = 'python /project/log_error_export.py -u http://%s:%s -t "%s,%s" -o %s' % (os.environ.get('NODE_HOST'), os.environ.get('ePort'), start_time, end_time, file_name)
        print cmd
        # judge if the log_collection has run over 15 minutes, if so return 0 to avoid effect the bubble_up
        now = datetime.datetime.now()
        delta = now-job_start_time
        print(delta)
        branch_name=os.environ.get("GERRIT_CHANGE_BRANCH",None)
        if  branch_name.startswith("rel-21") or branch_name.startswith("master"):
            if delta.seconds > 15*60:
                exit(0)
        if branch_name.startswith("rel-3."):
            exit(0)
        while retry_times < 3:
            result = os.system(cmd)
            if result == 0:
                break
            else:
                retry_times += 1
                time.sleep(120)
                
        if retry_times >= 3:
            print 'Exit the query due to a failed query:' + cmd
            break

    # merge *.csv files and save under save_dir
    save_dir = '/tmp/k8s_vora_log'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    #copy first csv file to save_file_name
    file_list = os.listdir(base_dir)
    file_list.sort()
    save_file_name = file_list[0]
    save_file_name = os.path.join(save_dir, save_file_name)
    with open(base_dir + '/' + file_list[0],'r+') as f :##handle with empty file 
        content = f.read()
        f.seek(0, 0)
        f.write('log_method,vsystem_datahub_sap_com_template,container_name,log_level,vsystem_datahub_sap_com_uuid,datahub_sap_com_app,log_class,log_component,namespace,tag,vsystem_datahub_sap_com_app,vsystem_datahub_sap_com_tenant,node_hostname,datahub_sap_com_app_component,log_topic,log_message,time_epoch,@timestamp,pod_name\n'+content)
        f.close()
    df = pd.read_csv(base_dir + '/' + file_list[0],low_memory=False)
    df.to_csv(save_file_name, index=False)
    
    # merge other csv files to save_file_name
    for i in range(1,len(file_list)):
        with open(base_dir + '/' + file_list[i],'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write('log_method,vsystem_datahub_sap_com_template,container_name,log_level,vsystem_datahub_sap_com_uuid,datahub_sap_com_app,log_class,log_component,namespace,tag,vsystem_datahub_sap_com_app,vsystem_datahub_sap_com_tenant,node_hostname,datahub_sap_com_app_component,log_topic,log_message,time_epoch,@timestamp,pod_name\n'+content)
            f.close()
        df = pd.read_csv(base_dir + '/'+ file_list[i],low_memory=False)
        print(file_list[i])
        df.to_csv(save_file_name, index=False, header=False, mode='a+')
    print "Kubernetes log collected for jobs and saved in ", save_file_name
    
    if retry_times >= 3:
        exit(1)
            
if __name__ == '__main__':
    print "Start to collect kubernetes log by elasticsearch..."
    main()