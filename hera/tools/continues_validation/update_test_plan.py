#!/usr/bin python
import requests
import os
import os.path
import time
import logging
import json
import datetime
from odtemUtility import ODTEMApi

check_interval = int(os.environ.get("CHECK_INTERVAL", 60))
max_error_retry_num = int(os.environ.get("MAX_ERROR_RETRY_NUM", 3))

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
api = ODTEMApi()

def runRequest(function, *args, **kwargs):
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
                logger.info( "Wait for %d seconds and retry" % check_interval)
                time.sleep(check_interval)
            else:
                logger.error( "Fail to make request for getting exceptions for %d seconds!" % max_error_retry_num)
                raise
        else:
            logger.debug( "Make request to server, return message is:\n status_code:%d,\n content:%s" % (ret.status_code, ret.content) )
            return ret

def getDate(days_ago):
    today = datetime.datetime.now()
    date_delta = datetime.timedelta(days = days_ago)
    start_date = today - date_delta
    return start_date.strftime('%Y-%m-%d')

def updateJobListOnDashboard(base_url, job_list, job_state, code_branch, use_for):
    url = base_url + "/api/v1/trd/updateJobState"
    request_json = {
        "environment": {
            "GERRIT_PROJECT": "hanalite-releasepack",
            "GERRIT_CHANGE_BRANCH": code_branch,
            "USE_FOR": use_for,
            "JOB_STATE": job_state,
            "JOB_LIST": job_list
        }
    }
    print "updateJobListOnDashboard: " + json.dumps(request_json)
    ret = runRequest(requests.post, url, json=request_json)
    if ret.status_code != 200:
        logger.error("Failed to update the job list status!")

def getJobsReadyToPromote(dataList, test_plan_name):
    jobs = []
    job_details = []
    #api = ODTEMApi()
    dev_test_plan_detail = api.getTestPlan(test_plan_name).json()
    for job in dataList:
        if job['job_state'].lower() == 'yes':
            print job['job_name']
            comp_name = api.findJobInTestPlan(job['job_name'], dev_test_plan_detail)
            if comp_name != None:
                jobs.append(job['job_name'])
                job_details.append({ 'case_name': job['job_name'], 'comp_name': comp_name })
    return jobs, job_details

def main():
    ## get job status
    dev_test_plan_use_for = os.environ.get("DEV_TEST_PLAN_USE_FOR", "NIGHTLY_VALIDATION_debug")
    dev_test_plan_name = json.loads(os.environ.get("DEV_TEST_PLAN_NAME", ""))
    formal_test_plan_use_for = os.environ.get("FORMAL_TEST_PLAN_USE_FOR", "NIGHTLY_VALIDATION")
    formal_test_plan_name = json.loads(os.environ.get("FORMAL_TEST_PLAN_NAME", ""))
    milestone_test_plan_name = json.loads(os.environ.get("MILESTONE_TEST_PLAN_NAME", ""))
    threshold = int(os.environ.get("THRESHOLD", "3"))
    check_days = int(os.environ.get("CHECK_DAYS", "7"))
    code_branch = os.environ.get("CODE_BRANCH", "master")
    start_date = getDate(check_days)  # 7 days ago
    #start_date = '2018-11-04'
    request_json = {
        "environment": {
            "GERRIT_PROJECT": "hanalite-releasepack",
            "GERRIT_CHANGE_BRANCH": code_branch,
            "USE_FOR": dev_test_plan_use_for
        },
        "result": {
            "start_date": start_date,
            "threshold": threshold
        }
    }
    base_url = os.environ.get("BASE_URL", "https://api.dashboard.datahub.only.sap:30711")
    url = base_url + "/api/v1/trd/summary/test"
    ret = runRequest(requests.post, url, json=request_json)
    if ret.status_code != 200:
        logger.error("Failed to get recent test status, exit!")
        return
    ret = ret.json()
    if ret['status'] != '200':
        logger.error("Failed to get recent test status, exit! Error message: %s" % ret['message'])
        return
    for platform in dev_test_plan_name:
        if platform in formal_test_plan_name.keys():
            jobs, job_details = getJobsReadyToPromote(ret['dataList'], dev_test_plan_name[platform])
            print "platform: " + platform + ", jobs: " + str(jobs)
            if len(jobs) > 0:
                api.addJobList(job_details, formal_test_plan_name[platform])
                if platform in milestone_test_plan_name:
                    api.addJobList(job_details, milestone_test_plan_name[platform])
                updateJobListOnDashboard(base_url, jobs, "enabled", code_branch, formal_test_plan_use_for)
                api.removeJobList(jobs, dev_test_plan_name[platform])
                updateJobListOnDashboard(base_url, jobs, "removed", code_branch, dev_test_plan_use_for)
        else:
            print "platform " + platform + " not in formal_test_plan, skipped to promote!"

    logger.info("Update test plan finished!")
    # update dashboard

if __name__ == "__main__":
    main()
