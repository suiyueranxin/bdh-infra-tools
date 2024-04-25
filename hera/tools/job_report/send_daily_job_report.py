#!/usr/bin/python
import requests
import datetime
import json
import sys

def sendDailyReport(for_test = True):
    """
    check if the job is existed in template
    """
    job_url = "https://api.dashboard.datahub.only.sap:30711/api/v1/trd/job/report"
    #job_url = "http://mo-00fad3fe7.mo.sap.corp:50011/api/v1/trd/job/report"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    data = {}
    data["typeList"] = ["NIGHTLY_VALIDATION","MILESTONE_VALIDATION","NIGHTLY_VALIDATION_update"]
    data["report_date"] = str(datetime.date.today())
    if for_test:
        data["receivers"] = ['lianjie.qin@sap.com']
    else:
        data["receivers"] = []
        data["file_bug"] = "true"
        data["for_debug"] = "false"
        data["with_bug_similarity"] = "false"


    try:
        r = requests.post(job_url, data=json.dumps(data), headers=headers, verify=False)
    except Exception,e:
        print e
        raise Exception('Fail to call send job report restApi.')
    if r.status_code != 200:
        raise Exception('Fail to get job report.')
    print "Send daily report for " + str(datetime.datetime.today())

if __name__ == '__main__':
    for_test = sys.argv[1]
    if for_test == 'True':
        sendDailyReport(True)
    else:
        sendDailyReport(False)
