#!/usr/bin/env python
import os
import sys
import json
from send_mail import SendEmail
import urllib2
import ssl
from urlparse import urlparse
import traceback
import datetime
import re
import copy
import requests
from slacklib import slack_message
from dateutil import parser
from datetime import timedelta

EMAIL_TITLE_PREFIX = "InfraBox job report: "
COMPARE_METHOD_STARTSWITH = 0
COMPARE_METHOD_ENDSWITH = 1

def updateURL(url):
    if "FIXED_INFRABOX_URL" in os.environ:
        fixedURL = os.environ['FIXED_INFRABOX_URL']
        parsed = urlparse(url)
        if parsed.netloc != fixedURL:
            replaced = parsed._replace(netloc=fixedURL)
            url = replaced.geturl()
    return url

def generateReport(jobs, gerritChangeURL, commitLog, voraVersion, dashboardURL, highlightFailure, voraMilestonePath):
    url = ''
    if 'INFRABOX_BUILD_URL' in os.environ:
        url = updateURL(os.environ['INFRABOX_BUILD_URL'])
    htmlTable = """
    <table border="1">
    <col width="200">
    <col width="300">
    <col width="300">
    <col width="80">
    <br><br><tr>
    <th colspan="1"><font size="2" face="Times" color= 0000CC>JOB NAME  </font></th>
    <th colspan="1"><font size="2" face="Times" color= 0000CC>START TIME</font></th>
    <th colspan="1"><font size="2" face="Times" color= 0000CC>END TIME</font></th>
    <th colspan="1"><font size="2" face="Times" color= 0000CC>STATUS</font></th>
    </tr>
    """
    for j in jobs:
        if os.environ.get('USE_FOR', "") == "DIS_VALIDATION_pr" and j['name'] == 'milestone-validations':
            continue
        stateStr = j['state']
        if highlightFailure and stateStr == 'failure':
            stateStr = "<font color=FF0000>%s</font>" % stateStr
        if highlightFailure and stateStr == 'unstable':
            stateStr = "<font color=orange>%s</font>" % stateStr
        if highlightFailure and stateStr == 'skipped':
            stateStr = "<font color=blue>%s</font>" % stateStr
        if highlightFailure and stateStr == 'finished':
            stateStr = "<font color=green>%s</font>" % stateStr

        htmlTable = htmlTable + """
        <tr>
        <td><a href=%s>%s</a></td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        </tr>
        """ % (url+"/job/"+j['raw_name'].replace("/", "%2F"),j['name'], j['start_date'], j['end_date'], stateStr)

    htmlTable = htmlTable + "</table>"
    gerritMessage = ''
    if gerritChangeURL is not None:
        gerritMessage = "<p>Gerrit code change URL: <a href=%s>%s</a></p><br>" % (gerritChangeURL, gerritChangeURL)

    voraVersionMessage = ''
    if voraVersion is not None:
        voraVersionMessage = "<p>Vora Version: %s</p><br>" % voraVersion

    voraAddressMessage = ''
    voraAddress = os.environ.get('VSYSTEM_ENDPOINT', '')
    if voraAddress is not None:
        voraAddressMessage = "<p>DI Address is: <a href=%s>%s</a></p><br>" % (voraAddress, voraAddress)

    SLC_BRIDGE_BASE_VERSION = None
    if "SLC_BRIDGE_BASE_VERSION" in os.environ:
        SLC_BRIDGE_BASE_VERSION = os.environ['SLC_BRIDGE_BASE_VERSION']
    SLCBVersionMessage = ''
    if SLC_BRIDGE_BASE_VERSION is not None:
        SLC_BRIDGE_BASE_VERSION = "<font color=FF0000>%s</font>" % SLC_BRIDGE_BASE_VERSION
        SLCBVersionMessage = "<p>SLCB Version: %s</p><br>" % SLC_BRIDGE_BASE_VERSION

    commitLogMessage = ''
    if commitLog is not None:
        commitLogMessage = "<p>Recent git commit logs can be found in the attachment.</p><br>"

    dashboardMessage = ''
    if dashboardURL is not None:
        dashboardMessage = "<p>If you need to do more actions, like job result analysis, tests error troubleshooting, bug report and management, please access BDH Dashboard:: <a href=%s>%s</a></p><br>" % (dashboardURL, dashboardURL)

    voraMilestonePathMessage = ''
    if voraMilestonePath is not None:
        voraMilestonePathMessage = "<p>Vora milestone path: <a href=%s>%s</a></p><br>" % (voraMilestonePath, voraMilestonePath)

    Report = """\
     <html>
       <head></head>
      <body>
        <p>Dear colleagues,</p>
        <br>
        <p>Here are infrabox jobs execution report. For details, please refer to:<a href=%s> Infrabox jobs dashboard</a>
        </p> <br>
        %s
        %s
        %s
        %s
        %s
        %s
        %s
        %s
        <br><br><br>
        <p>Best regards, </p>
        <p>SAP Data Intelligence Infrastructure Xi&#39an Team</p>
      </body>
     </html>
     """ % (url, voraAddressMessage, gerritMessage, voraVersionMessage, SLCBVersionMessage, commitLogMessage, dashboardMessage, voraMilestonePathMessage, htmlTable)
    return Report

def sendDefaultReceiverJobReport(job, subTitle, sendDefaultAlways, defaultReceivers, gerritChangeURL, commitLog, voraVersion, dashboardURL, voraMilestonePath):
    if defaultReceivers is None or len(defaultReceivers) == 0:
        return
    receivers = defaultReceivers
    success = True
    jobs = job.get('parent_jobs', [])

    for j in jobs:
        if j['state'] == 'finished':
            pass
        elif j['state'] == 'failure':
            success = False
        elif j['state'] == 'running':
            pass
        elif j['state'] == 'skipped':
            pass
        else:
            success = False

    if sendDefaultAlways:
        success = False

    if success:
        #no notification
        print ("Successfully finished build")
    else:
        mail = SendEmail('mail.sap.corp')
        receiverSets = set(receivers)
        receivers = list(receiverSets)
        print (receivers)
        if commitLog is None:
            mail.sendTxtMail(receivers, EMAIL_TITLE_PREFIX + subTitle, generateReport(jobs, gerritChangeURL, commitLog, voraVersion, dashboardURL, True, voraMilestonePath))
        else:
            if isinstance(commitLog, list):
                subTitle = os.environ['USE_FOR']
                if subTitle == "AUTO_ENV":
                    mail.sendAttachMail(receivers, EMAIL_TITLE_PREFIX + subTitle, generateReportForAUTOENV(jobs, gerritChangeURL, commitLog, voraVersion, dashboardURL, False, voraMilestonePath), commitLog)
                else:
                    mail.sendAttachMail(receivers, EMAIL_TITLE_PREFIX + subTitle, generateReport(jobs, gerritChangeURL, commitLog, voraVersion, dashboardURL, False, voraMilestonePath), commitLog)
            else:
                mail.sendAttachMail(receivers, EMAIL_TITLE_PREFIX + subTitle, generateReport(jobs, gerritChangeURL, commitLog, voraVersion, dashboardURL, False, voraMilestonePath), [commitLog])

def updateReceiverJobs(job, component, receiverJobs, lastSuccess, compareMethod):
    success = True
    jobs = job.get('parent_jobs', [])

    for j in jobs:
        compareResult = False
        if compareMethod == COMPARE_METHOD_STARTSWITH:
            compareResult = j['name'].startswith(component)
        elif compareMethod == COMPARE_METHOD_ENDSWITH:
            compareResult = j['name'].endswith(component)

        if compareResult:
            receiverJobs.append(j)
            if j['state'] == 'finished':
                pass
            elif j['state'] == 'failure':
                success = False
            elif j['state'] == 'running':
                pass
            elif j['state'] == 'skipped':
                pass
            else:
                success = False
    return success and lastSuccess

def sendComponentReceiverJobReport(job, subTitle, componentReceivers, gerritChangeURL, commitLog, voraVersion, dashboardURL, voraMilestonePath):
    if componentReceivers is None or len(componentReceivers) == 0:
        return

    # get all receivers
    receiversDict = {}
    for r in componentReceivers:
        componentName = r['name']
        componentEmails = r['receivers'].split(',')
        for email in componentEmails:
            if email not in receiversDict:
                receiversDict[email] = []
            receiversDict[email].append(componentName)
    for receiver, componentNames in receiversDict:# pylint: disable=bad-option-value,dict-iter-missing-items
        success = True
        receiverJobs = []
        for component in componentNames:
            success = updateReceiverJobs(job, component, receiverJobs, success, COMPARE_METHOD_STARTSWITH)
        if not success:
            receivers = [ receiver ]
            mail = SendEmail('mail.sap.corp')
            if commitLog is None:
                mail.sendTxtMail(receivers, EMAIL_TITLE_PREFIX + subTitle, generateReport(receiverJobs, gerritChangeURL, commitLog, voraVersion, dashboardURL, True, voraMilestonePath))
            else:
                mail.sendAttachMail(receivers, EMAIL_TITLE_PREFIX + subTitle, generateReport(receiverJobs, gerritChangeURL, commitLog, voraVersion, dashboardURL, True, voraMilestonePath), [ commitLog ])

def generateReportForAUTOENV(jobs, gerritChangeURL, commitLog, voraVersion, dashboardURL, highlightFailure, voraMilestonePath):
    url = ''
    if 'INFRABOX_BUILD_URL' in os.environ:
        url = updateURL(os.environ['INFRABOX_BUILD_URL'])
    htmlTable = """
    <table border="1">
    <col width="200">
    <col width="300">
    <col width="300">
    <col width="80">
    <br><br><tr>
    <th colspan="1"><font size="2" face="Times" color= 0000CC>JOB NAME  </font></th>
    <th colspan="1"><font size="2" face="Times" color= 0000CC>START TIME</font></th>
    <th colspan="1"><font size="2" face="Times" color= 0000CC>END TIME</font></th>
    <th colspan="1"><font size="2" face="Times" color= 0000CC>STATUS</font></th>
    </tr>
    """
    k8sCreateJob=''
    installJob=''
    testJobs=''
    logJob=''
    upgradeJob=''
    for j in jobs:
        stateStr = j['state']
        tr = """
        <tr>
        <td><a href=%s>%s</a></td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        </tr>
        """ % (url+"/job/"+j['raw_name'].replace("/", "%2F"),j['name'], j['start_date'], j['end_date'], stateStr)
        if highlightFailure and stateStr == 'failure':
            stateStr = "<font color=FF0000>%s</font>" % stateStr
        jobName = j['name']
        if "k8s_creation" in jobName:
            k8sCreateJob = tr
        elif "install_" in jobName:
            installJob = tr
        elif "e2e" in jobName or "test" in jobName:
            testJobs = testJobs + tr
        elif "log" in jobName:
            logJob = tr
        elif "upgrade" in jobName:
            upgradeJob = tr
    htmlTable = htmlTable + k8sCreateJob + installJob + upgradeJob + testJobs + logJob + "</table>"

    voraVersionMessage = ''
    if voraVersion is not None:
        voraVersionMessage = "<p>Vora Version: %s</p><br>" % voraVersion

    voraAddressMessage = ''
    voraAddress = os.environ.get('VSYSTEM_ENDPOINT', '')
    if voraAddress is not None:
        voraAddressMessage = "<p>DI Address is: <a href=%s>%s</a></p><br>" % (voraAddress, voraAddress)

    SLC_BRIDGE_BASE_VERSION = None
    if "SLCB_VERSION" in os.environ:
        SLC_BRIDGE_BASE_VERSION = os.environ['SLCB_VERSION']
    SLCBVersionMessage = ''
    if SLC_BRIDGE_BASE_VERSION is not None:
        SLC_BRIDGE_BASE_VERSION = "<font color=FF0000>%s</font>" % SLC_BRIDGE_BASE_VERSION
        SLCBVersionMessage = "<p>SLCB Version: %s</p><br>" % SLC_BRIDGE_BASE_VERSION

    Report = """\
     <html>
       <head></head>
      <body>
        <p>Dear colleagues,</p>
        <br>
        <p>Here are auto deploy DI environment report. For details, please refer to:<a href=%s> Infrabox jobs dashboard</a>
        </p> <br>
        %s
        %s
        %s
        %s
        <br><br><br>
        <p>Best regards, </p>
        <p>SAP Data Intelligence AUTO ENV Team</p>
      </body>
     </html>
     """ % (url, voraAddressMessage, voraVersionMessage, SLCBVersionMessage, htmlTable)
    return Report

def sendPlatformReceiverJobReport(job, subTitle, platformReceivers, gerritChangeURL, commitLog, voraVersion, dashboardURL, voraMilestonePath):
    if platformReceivers is None or len(platformReceivers) == 0:
        return

    receiversDict = {}
    for r in platformReceivers:
        platformName = r['name']
        platformEmails = r['receivers'].split(',')
        for email in platformEmails:
            if email not in receiversDict:
                receiversDict[email] = []
            receiversDict[email].append(platformName)
    for receiver, platformNames in receiversDict: # pylint: disable=bad-option-value,dict-iter-missing-items
        success = True
        receiverJobs = []
        for platform in platformNames:
            success = updateReceiverJobs(job, platform, receiverJobs, success, COMPARE_METHOD_ENDSWITH)
        if not success:
            mail = SendEmail('mail.sap.corp')
            receivers = [ receiver ]
            if commitLog is None:
                mail.sendTxtMail(receivers, EMAIL_TITLE_PREFIX + subTitle, generateReport(receiverJobs, gerritChangeURL, commitLog, voraVersion, dashboardURL, True, voraMilestonePath))
            else:
                mail.sendAttachMail(receivers, EMAIL_TITLE_PREFIX + subTitle, generateReport(receiverJobs, gerritChangeURL, commitLog, voraVersion, dashboardURL, True, voraMilestonePath), [ commitLog ])

def parseMilestonePathRepoType(voraMilestonePath):
    matchObj = re.match(r'https://int.repositories.cloud.sap/artifactory/(.*)/com/sap/datahub/SAPDataHub/(.*)', voraMilestonePath, re.M|re.I)
    if matchObj:
        return matchObj.group(1)
    return None

def isGrouped(name):
    grouped_jobs = 'install|k8s_creation|dhaas_creation|uninstall|log_collection|k8s_deletion|dhaas_deletion'
    reObj = re.search(grouped_jobs, name)
    if bool(reObj):
        splited_job_name = name.split('_')
        if len(splited_job_name) >= 2:
            try:
                int(splited_job_name[-1])
                return True
            except Exception as e:
                print ("Job is not grouped from job name with exception: " + str(e))
            return False
    return False

def getJobNameAndPlatform(jobName):
    name = None
    platform = None
    validation_type = None
    full_platforms_str = 'monsoon|gke|kops|aks|gardener_aws|eks|dhaas_aws'
    full_platforms_pattern = '(' + full_platforms_str + ')$'
    full_service_plan_str = 'ccm|dwctrial|dwc|hc'
    full_service_plans_pattern = '(' + full_service_plan_str + ')$'
    # vora_tools_ui_e2e_test_di_on_prem-aks
    if os.getenv("LANDSCAPE_NAME", "") != "":
        if os.environ["LANDSCAPE_NAME"] in jobName:
            index = jobName.index(os.environ["LANDSCAPE_NAME"])
            name = jobName[0:(index - 1)]
        else:
            reObj = re.search(full_service_plans_pattern, jobName)
            if bool(reObj):
                name = jobName[0:len(jobName) - len(reObj.group(0)) - 1]
                platform = reObj.group(0)
                if isGrouped(name):
                    #if there is group info in job name, remove it
                    name = '_'.join(name.split('_')[:-1])
            else:        
                name = jobName

    elif "_test_" in jobName and "-" in jobName:
        index = jobName.index('-')
        platform = jobName[index+1:]
        index2 = jobName.index('_test')
        name = jobName[0:index2 + 5]
        validation_type = jobName[index2 + 6:index]
        if not validation_type:
            validation_type = None
        if platform not in full_platforms_str.split('|'):
            reObj = re.search(full_platforms_pattern, platform)
            if bool(reObj):
                platform = reObj.group(0)
    elif "_test_" in jobName:
        index = jobName.index('_test')
        name = jobName[0:index + 5]
        platform = jobName[index + 6:]
    else:
        reObj = re.search(full_platforms_pattern, jobName)
        if bool(reObj):
            name = jobName[0:len(jobName) - len(reObj.group(0)) - 1]
            platform = reObj.group(0)
            if isGrouped(name):
                #if there is group info in job name, remove it
                name = '_'.join(name.split('_')[:-1])
    return name, platform, validation_type

def generateJsonObject(jobs, commitFilePath, voraVersion, useFor, voraMilestonePath, componentVersions):
    jsonObj = copy.deepcopy(jobs)
    jsonObj['build']['url'] = updateURL(jsonObj['build']['url'])

    commitObj = []
    if os.path.isfile(commitFilePath):
        commitObj = json.load(open(commitFilePath, 'r'))

    jsonObj["commit_history"] = commitObj
    jsonObj["environment"] = {}
    if useFor != "DIS_VALIDATION_pr":
        jsonObj["environment"]["VORA_VERSION"] = voraVersion

    if useFor == "DIS_VALIDATION_pr":
        try:
            if "LANDSCAPE_NAME" not in os.environ:
                job = json.load(open('/infrabox/job.json', 'r'))
                job_report_name = job['job']['name']
                landscape_name = job_report_name.split('/')[-1].split('.')[0][11:]
                os.environ['LANDSCAPE_NAME'] = landscape_name

            if os.environ["LANDSCAPE_NAME"].find('-infrabox') > -1:
                index = os.environ["LANDSCAPE_NAME"].index('-infrabox')
                jsonObj["environment"]["LANDSCAPE"] = os.environ["LANDSCAPE_NAME"][0:(index)]
            elif os.environ["LANDSCAPE_NAME"].find('-pool') > -1:
                index = os.environ["LANDSCAPE_NAME"].index('-pool')
                jsonObj["environment"]["LANDSCAPE"] = os.environ["LANDSCAPE_NAME"][0:(index)]
            else:
                jsonObj["environment"]["LANDSCAPE"] = os.environ["LANDSCAPE_NAME"]
        except Exception as e:
            print (str(e))
            exit(1)

    jsonObj["environment"]['JOB_NAME'], jsonObj["environment"]['JOB_PLATFORM'], jobValidationType = getJobNameAndPlatform(jobs['job']['name'])

    if jobValidationType:
        jsonObj["environment"]['JOB_VALIDATION_TYPE'] = jobValidationType

    if 'FULL_PLATFORM' in os.environ:
        jsonObj["environment"]["full_platform"] = os.environ['FULL_PLATFORM'].split(',')

    if 'K8S_VERSION' in os.environ:
        jsonObj["environment"]["K8S_VERSION"] = os.environ['K8S_VERSION']

    if 'K8S_CLUSTER_NAMES' in os.environ:
        jsonObj["environment"]["K8S_CLUSTER_NAME"] = {}
        for item in os.environ['K8S_CLUSTER_NAMES'].split(','):
            jsonObj["environment"]["K8S_CLUSTER_NAME"][item.split(':')[0]] = item.split(':')[-1]
    elif 'K8S_CLUSTER_NAME' in os.environ:
        jsonObj["environment"]["K8S_CLUSTER_NAME"] = '{' + os.environ['K8S_CLUSTER_NAME'] + '}'

    if 'BASE_BDH_VERSIONS' in os.environ:
        jsonObj["environment"]["RAW_VORA_VERSION"] = os.environ['BASE_BDH_VERSIONS']

    if 'VSYSTEM_ENDPOINT' in os.environ:
        jsonObj["environment"]["VSYSTEM_ENDPOINT"] = os.environ['VSYSTEM_ENDPOINT']

    if 'VORA_TENANT' in os.environ:
        jsonObj["environment"]["VORA_TENANT"] = os.environ['VORA_TENANT']

    if 'VORA_USERNAME' in os.environ:
        jsonObj["environment"]["VORA_USERNAME"] = os.environ['VORA_USERNAME']

    if 'VORA_PASSWORD' in os.environ:
        jsonObj["environment"]["VORA_PASSWORD"] = os.environ['VORA_PASSWORD']

    if 'VORA_SYSTEM_TENANT_PASSWORD' in os.environ:
        jsonObj["environment"]["VORA_SYSTEM_TENANT_PASSWORD"] = os.environ['VORA_SYSTEM_TENANT_PASSWORD']

    if 'INFRABOX_JOB_API_URL' in os.environ:
        jsonObj["environment"]["INFRABOX_JOB_API_URL"] = os.environ['INFRABOX_JOB_API_URL']

    if 'NAMESPACE' in os.environ:
        jsonObj["environment"]["NAMESPACE"] = os.environ['NAMESPACE']

    if 'DEPLOY_TYPE' in os.environ:
        jsonObj["environment"]["DEPLOY_TYPE"] = os.environ['DEPLOY_TYPE']

    jsonObj["environment"]["USE_FOR"] = useFor
    jsonObj["environment"]["INFRABOX_BUILD_RESTART_COUNTER"] = os.environ['INFRABOX_BUILD_RESTART_COUNTER']

    if useFor != "DIS_VALIDATION_pr":
        jsonObj["environment"]["GERRIT_PROJECT"] = "hanalite-releasepack"
        if jsonObj['project']['name'] in [ "hanalite" ]:
            jsonObj["environment"]["GERRIT_PROJECT"] = "hanalite"
    else:
        jsonObj["environment"]["GERRIT_PROJECT"] = "dis-release"

    if componentVersions:
        jsonObj['environment']['COMPONENT_VERSIONS'] = componentVersions

    if "GERRIT_PATCHSET_REF" in os.environ:
        jsonObj["environment"]["GERRIT_PATCHSET_REF"] = os.environ["GERRIT_PATCHSET_REF"]

    if "GERRIT_CHANGE_OWNER_USERNAME" in os.environ:
        jsonObj["environment"]["GERRIT_CHANGE_OWNER_USERNAME"] = os.environ["GERRIT_CHANGE_OWNER_USERNAME"]

    if "GERRIT_CHANGE_BRANCH" in os.environ:
        jsonObj["environment"]["GERRIT_CHANGE_BRANCH"] = os.environ["GERRIT_CHANGE_BRANCH"]

    if "GERRIT_CHANGE_URL" in os.environ:
        jsonObj["environment"]["GERRIT_CHANGE_URL"] = os.environ["GERRIT_CHANGE_URL"]

    if "IMAGE_NAME" in os.environ:
        jsonObj["environment"]["IMAGE_NAME"] = os.environ["IMAGE_NAME"]

    if "IMAGE_TAG" in os.environ:
        jsonObj["environment"]["IMAGE_TAG"] = os.environ["IMAGE_TAG"]

    if "USER_NAME" in os.environ:
        jsonObj["environment"]["USER_NAME"] = os.environ["USER_NAME"]

    if ("GITHUB_PULL_REQUEST_NUMBER" in os.environ) and ("GITHUB_REPOSITORY_FULL_NAME" in os.environ) :
        jsonObj["environment"]["GITHUB_PULL_REQUEST_NUMBER"] = os.environ["GITHUB_PULL_REQUEST_NUMBER"]
        pr_title, pr_label = get_PR_title_label(os.environ["GITHUB_REPOSITORY_FULL_NAME"], os.environ["GITHUB_PULL_REQUEST_NUMBER"])
        jsonObj["environment"]["GITHUB_PULL_REQUEST_TITLE"] = pr_title
        jsonObj["environment"]["GITHUB_PULL_REQUEST_LABEL"] = pr_label
    if "GITHUB_PULL_REQUEST_BASE_SHA" in os.environ:
        jsonObj["environment"]["GITHUB_PULL_REQUEST_BASE_SHA"] = os.environ["GITHUB_PULL_REQUEST_BASE_SHA"]

    if "GITHUB_PULL_REQUEST_URL" in os.environ:
        jsonObj["environment"]["GITHUB_PULL_REQUEST_URL"] = os.environ["GITHUB_PULL_REQUEST_URL"]

    if "DIS_VERSION" in os.environ:
        jsonObj["environment"]["DIS_VERSION"] = os.environ["DIS_VERSION"]

    if useFor == "MILESTONE_VALIDATION_e2e":
        if "INFRABOX_CRONJOB_NAME" in os.environ: 
            if os.environ["INFRABOX_CRONJOB_NAME"].find('bi_weekly_run') > -1:
                jsonObj["environment"]["FREQUENCY_TYPE"] = 'bi_weekly'
            else:
                jsonObj["environment"]["FREQUENCY_TYPE"] = 'weekly' 
        else:
            jsonObj["environment"]["FREQUENCY_TYPE"] = ''

    if voraMilestonePath is not None:
        jsonObj["environment"]["VORA_MILESTONE_PATH"] = voraMilestonePath
        repoType = parseMilestonePathRepoType(voraMilestonePath)
        if repoType:
            jsonObj["environment"]["VORA_MILESTONE_PATH_REPO_TYPE"] = repoType
    # add total case change alert option
    jsonObj["total_case_change"] = "true"
    # add testruns section
    jsonObj["test_runs"] = getTestCaseResult(jobs)

    # parse test case name and platform
    if useFor == "DIS_VALIDATION_pr":
        for job in jsonObj["parent_jobs"]:
            job['test_job_name'], job['test_job_platform'], testJobValidationType = getJobNameAndPlatform(job['name'])
            if testJobValidationType:
                job['test_job_validation_type'] = testJobValidationType
            job = addErrorMsgs(job)
    else:
        for job in jsonObj["parent_jobs"]:
            job['test_job_name'], job['test_job_platform'], testJobValidationType = getJobNameAndPlatform(job['name'])
            if testJobValidationType:
                job['test_job_validation_type'] = testJobValidationType
            if job['test_job_platform'] and job['test_job_platform'] == "gke" and 'GKE_LATEST_K8S_VERSION' in os.environ:
                jsonObj["environment"]["K8S_VERSION"] = os.environ['GKE_LATEST_K8S_VERSION']

    return jsonObj

def addErrorMsgs(job):

    infrabox_job_api_base = os.environ["INFRABOX_JOB_API_URL"].rsplit('/', 1)[0]
    job_archive_url = updateURL(infrabox_job_api_base + '/' + job['id'] + '/archive')
    download_url = job_archive_url + '/download?filename=/archive/error_msg.log'
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib2.Request(download_url)
    req.add_header('Content-Type', 'application/json')
    if os.getenv("INFRABOX_API_TOKEN", "") != "":
        token = 'bearer ' + os.environ["INFRABOX_API_TOKEN"]
        req.add_header('Authorization', token)
    try:
        response = urllib2.urlopen(req, context=ctx)
        error_msgs = response.readlines()
        if "The requested URL was not found on the server" in error_msgs[0]:
            error_msgs = ""
        response.close()
    except Exception as e:
        print (str(e))
        error_msgs = ""

    if error_msgs == "":
        return job
    job['error_msg'] = {}
    for msg in error_msgs:
        key = msg.split(":")[0].strip()
        value = msg.split(":")[1].strip()
        job["error_msg"][key] = value

    return job

def getTestCaseResult(data):
    """
    Get test case result details
    """
    test_runs_list = []

    infrabox_job_api_base = os.environ["INFRABOX_JOB_API_URL"].rsplit('/', 1)[0]
    for job in data['parent_jobs']:
        job_name = job['name']

        job_raw_name = job['raw_name'] if 'raw_name' in job else job_name
        if 'test' not in job_name:
            continue
        if os.environ["USE_FOR"] == "DIS_VALIDATION_pr" and '_test_' not in job_name:
            continue

        job_id = job['id']
        job_console_url = updateURL(infrabox_job_api_base + '/' + job_id + '/console')
        job_testruns_url = updateURL(infrabox_job_api_base + '/' + job_id + '/testruns')

        print(job_console_url)
        print(job_testruns_url)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            req = urllib2.Request(job_testruns_url)
            req.add_header('Content-Type', 'application/json')
            if os.getenv("INFRABOX_API_TOKEN", "") != "":
                token = 'bearer ' + os.environ["INFRABOX_API_TOKEN"]
                req.add_header('Authorization', token)

            response = urllib2.urlopen(req, context=ctx)
            response_data = response.read().rstrip('\n')
            response_data = json.loads(response_data)
            job_testcase_list = [ (item['name'],item['suite']) for item in response_data]
            job_testcase_list = set(job_testcase_list)
            job_test_runs = []
            verbose_output = os.environ.get("VERBOSE", "0")
            for test in job_testcase_list:
                test_result_list = [ item for item in response_data if item['name'] == test[0] and item['suite'] == test[1]]
                sorted_test_result_list = sorted( test_result_list, key=lambda item: datetime.datetime.strptime(item['timestamp'], "%Y-%m-%d %H:%M:%S"), reverse=True)
                if verbose_output == "1":
                    print ("For test '%s' in test suite '%s', there is(are) %d execution record(s):" % (test[0], test[1], len(sorted_test_result_list)))
                    print ("----------------------------")
                    for record in sorted_test_result_list:
                        print (record)
                    print ("----------------------------")
                job_test_runs.append(sorted_test_result_list[0])

            if "_test_" in job_name:
                test_job_name, test_job_platform, test_job_valdiation_type = getJobNameAndPlatform(job_name)
                test_meta_data =  {'job_name': job_name, 'test_job_name': test_job_name, 'test_job_platform': test_job_platform, 'job_id': job_id, 'job_console_url': job_console_url, 'job_test_runs': job_test_runs, 'raw_name': job_raw_name}
                if test_job_valdiation_type:
                    test_meta_data['test_job_valdiation_type'] = test_job_valdiation_type
                test_runs_list.append(test_meta_data)
            elif os.getenv("LANDSCAPE_NAME", "") != "":
                test_job_name, test_job_platform, test_job_valdiation_type = getJobNameAndPlatform(job_name)
                test_meta_data =  {'job_name': job_name, 'test_job_name': test_job_name, 'job_id': job_id, 'job_console_url': job_console_url, 'job_test_runs': job_test_runs, 'raw_name': job_raw_name}
                if test_job_valdiation_type:
                    test_meta_data['test_job_valdiation_type'] = test_job_valdiation_type
                test_runs_list.append(test_meta_data)
            else:
                test_runs_list.append({'job_name': job_name, 'job_id': job_id, 'job_console_url': job_console_url, 'job_test_runs': job_test_runs, 'raw_name': job_raw_name})
        except Exception:
            print ("Error when getting test run: " + job_testruns_url)
            traceback.print_exc(file=sys.stdout)

    return test_runs_list

def sendReportToRestAPI(restAPIHost, restAPIPort, restAPIPath, jsonObj):
    if not restAPIPort:
        url = restAPIHost + restAPIPath
    else:
        url = restAPIHost + ':' + restAPIPort + restAPIPath
    retry = 1
    sendSuccess = False
    while retry <= 3:
        print ("Try to sendReportToRestApi: [" + str(retry) +"/3]")
        ret = requests.post(url, verify=False, json=jsonObj)
        print ("sendReportToRestAPI response code: " + str(ret.status_code))
        print ("sendReportToRestAPI response content: " + str(ret.content))
        if ret.status_code in [200, 201]:
            print ("sendReportToRestApi success")
            sendSuccess = True
            break
        if ret.status_code in [400, 403]:
            print("sendReportToRestApi Failed, Rest API server interal error: " + str(ret.content))
            sendSuccess = False
            break
        retry += 1
    if not sendSuccess:
        raise Exception("sendReportToRestApi failed, will exit")
def getJobJsonFromRestAPI(restAPIHost, restAPIPort, restAPIPath, manuallyBuildNumber, manuallyRestartCounter, useFor, componentVersions):
    if not restAPIPort:
        url = restAPIHost + restAPIPath
    else:
        url = restAPIHost + ':' + restAPIPort + restAPIPath

    requestObj = {}
    requestObj['environment'] = {}
    if useFor == "DIS_VALIDATION_pr":
        requestObj['environment']['GERRIT_PROJECT'] = 'hanalite-releasepack'
    else:
        requestObj['environment']['GERRIT_PROJECT'] = 'dis-release'
    requestObj['environment']['INFRABOX_BUILD_NUMBER'] = manuallyBuildNumber
    requestObj['environment']['INFRABOX_BUILD_RESTART_COUNTER'] = manuallyRestartCounter
    requestObj['environment']['USE_FOR'] = useFor
    if componentVersions:
        requestObj['environment']['COMPONENT_VERSIONS'] = componentVersions
    requestObj['result'] = {}
    requestObj['result']['expected_records'] = 1

    job = None

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/json')
        jsonContent = json.dumps(requestObj)
        print (jsonContent)
        response = urllib2.urlopen(req, jsonContent, context=ctx)
        jobObj = json.load(response)
        if 'raw_data' in jobObj.keys() and 'parent_jobs' in jobObj['raw_data'].keys():
            job = jobObj['raw_data']
        else:
            print ("No parent_jobs!")
    except Exception:
        print ("Error when getting job.json, return None.")
        traceback.print_exc(file=sys.stdout)

    return job

def generateReportEmailError(reason):
    url = ''
    if 'INFRABOX_BUILD_URL' in os.environ:
        url = updateURL(os.environ['INFRABOX_BUILD_URL'])
    else:
        print ('generateReportEmailError: INFRABOX_BUILD_URL is empty, return error.')
        return None
    Report = """\
    <html>
      <head></head>
      <body>
        <p>Dear colleagues,</p>
        <br>
        <p>There's an error happens when inserting data to TRD system, which needs to be tracking. For details, please refer to: <a href=%s>%s</a> </p> <br>
        <br><br>
        <p>Best regards, </p>
        <p>BDH Infrastructure Xi&#39an Team</p>
      </body>
    </html>
    """ % (url, url)
    return Report

def sendReportToRestAPIErrorEmail(reason):
    emailContent = generateReportEmailError(reason)
    if not emailContent:
        print ('## generate report email error, content is none!')
        return
    mail = SendEmail('mail.sap.corp')
    receivers = ['lianjie.qin@sap.com', 'edward.wang@sap.com', 'max.zhang@sap.com', 'jing.li08@sap.com']
    mail.sendTxtMail(receivers, 'Infrabox notifiation: error when inserting data to TRD', emailContent)

def generateInstallJobError(reason):
    url = ''
    if 'INFRABOX_BUILD_URL' in os.environ:
        url = updateURL(os.environ['INFRABOX_BUILD_URL'])
    else:
        print ('generateInstallJobError: INFRABOX_BUILD_URL is empty, return error.')
        return None
    Report = """\
    <html>
      <head></head>
      <body>
        <p>Dear colleagues,</p>
        <br>
        <p>There's an error happens in build/create/install job of nightly/milestone validation. For details, please refer to: <a href=%s>%s</a> </p> <br>
        <br><br>
        <p>Best regards, </p>
        <p>BDH Infrastructure Xi&#39an Team</p>
      </body>
    </html>
    """ % (url, url)
    return Report

def sendReportToInstallJobErrorEmail(reason):
    emailContent = generateInstallJobError(reason)
    if not emailContent:
        print ('## generate report email error, content is none!')
        return
    mail = SendEmail('mail.sap.corp')
    receivers = [ 'lianjie.qin@sap.com', 'edward.wang@sap.com', 'max.zhang@sap.com' ]
    mail.sendTxtMail(receivers, 'Infrabox notifiation: build/create/install job error in night/milestone validation ', emailContent)

def setupClusterSucceed(data, subTitle):
    """
    Return whether build/create/install jobs succeed or not
    """
    if subTitle == "MILESTONE_VALIDATION":
        pattern = re.compile(r'k8s_creation_.*|install_.*')
    elif subTitle == "DIS_VALIDATION_pr":
        pattern = re.compile(r'build-test-*|deploy-test-*|validate-test-*')
    else:
        pattern = re.compile(r'bdh-infra-tools/build$|bdh-infra-tools/k8s_creation_.*|bdh-infra-tools/install_.*')

    for job in data['parent_jobs']:
        job_name = job['name']
        if pattern.match(job_name) is not None and job['state'] != 'finished':
            print ("job %s failed!" % job_name)
            return False
    return True

def filterSingleJobName(jobName):
    tmp = jobName.split('/')
    jobName = tmp[len(tmp)-1]
    matchObj = re.match(r"(.+)\.(\d+)", jobName, re.M|re.I)
    if matchObj:
        jobName = matchObj.group(1)
    return jobName

def filterJobsName(jobs):
    """
    Filter the job name which is endded by .*
    also filter job name with /
    """
    if 'job' in jobs and 'name' in jobs['job']:
        jobs['job']['raw_name'] = jobs['job']['name']
        jobs['job']['name'] = filterSingleJobName(jobs['job']['name'])

    if 'parent_jobs' in jobs:
        for job in jobs['parent_jobs']:
            if 'name' in job:
                job['raw_name'] = job['name']
                job['name'] = filterSingleJobName(job['name'])
            if 'depends_on' in job and job['depends_on'] is not None:
                for dependsJobs in job['depends_on']:
                    if 'job' in dependsJobs:
                        dependsJobs['raw_job'] = dependsJobs['job']
                        dependsJobs['job'] = filterSingleJobName(dependsJobs['job'])
    return jobs

def get_creation_job_info(jobs):
    creation_job_info = {'name': '', 'state':'', 'job_url':'', 'id':''}
    if len(jobs) == 0:
        return creation_job_info
    for j in jobs:
        if 'name' in j and ('creation' in j['name'] or 'smoke-tests-setup' in j['name']):
            creation_job_info['name'] = j['name']
            if 'state' in j:
                creation_job_info['state'] = j['state']
            if 'raw_name' in j:
                creation_job_info['job_url'] = j['raw_name'].replace('/', "%2F")
            if 'id' in j:
                creation_job_info['id'] = j['id'].replace('/', "%2F")
            break
    return creation_job_info

def get_admin_conf(job_api_url, job_id):
    if job_api_url == '' or job_id =='':
        return ''
    admin_conf_url = ''
    url_list = job_api_url.split('/')
    prefix_url = '/'.join(url_list[:-1])
    if os.environ.get("USE_FOR", "") != "DIS_VALIDATION_pr":
        admin_conf_url = prefix_url + '/'+ job_id + '/archive/download?filename=archive/admin.conf&view=false'
    else:
        admin_conf_url = prefix_url + '/'+ job_id + '/archive/download?filename=archive/shoot-kubeconfig.conf&view=false'
    return admin_conf_url

def get_ugrade_info(job_name, base_versions_list, vora_version):
    upgrade_from, upgrade_to = base_versions_list[0], vora_version
    job_index_str = job_name.split('system_upgrade_')[1]
    re_group = re.match('[0-9]+', job_index_str)
    if re_group:
        job_index = int(re_group.group())
        upgrade_from = base_versions_list[job_index - 1]
        upgrade_to = vora_version if job_index == len(base_versions_list) else base_versions_list[job_index]
    else:
        upgrade_from = base_versions_list[0]
        upgrade_to = vora_version
    return upgrade_from, upgrade_to

def get_restored_cluster_info(job, job_api_url, current_job_url):
    if not 'name' in job or not 'id' in job:
        return None
    if not os.path.exists('/infrabox/inputs/' + job['name'] + '/k8s_cluster.txt'):
        return None
    restored_cluster = {'name': None, 'admin_conf': None}
    with open('/infrabox/inputs/' + job['name'] + '/k8s_cluster.txt') as f:
        restored_cluster['name'] = f.read().strip()
    restored_cluster['admin_conf'] = get_admin_conf(job_api_url, job['id'])

    restored_cluster_info = ''
    if restored_cluster is not None:
        restored_cluster_info = '\n- Restored cluster infomation:\
        \n>Cluster for restore job: <{}|url>\
        \n>Cluster name for restore: `{}`\
        \n>Download kube config of cluster for restore: <{}|admin.conf>\n'.format(current_job_url, restored_cluster['name'], restored_cluster['admin_conf'])

    return restored_cluster_info

def get_restored_tenant_info(job_name):
    if not os.path.exists('/infrabox/inputs/' + job_name + '/env.sh'):
        return None
    restored_tenant = {
        'endpoint': None,
        'default_tenant': None,
        'default_tenant_pwd': None,
        'system_tenant': None,
        'system_tenant_pwd': None
        }
    with open('/infrabox/inputs/' + job_name + '/env.sh') as f:
        for line in f.readlines():
            if 'VORA_SYSTEM_TENANT=' in line:
                restored_tenant['system_tenant'] = line.split('=')[1].strip()
            elif 'VORA_SYSTEM_TENANT_PASSWORD' in line:
                restored_tenant['system_tenant_pwd'] = line.split('=')[1].strip()
            elif 'VSYSTEM_ENDPOINT=' in line:
                restored_tenant['endpoint'] = line.split('=')[1].strip()
            elif 'VORA_TENANT=' in line:
                restored_tenant['default_tenant'] = line.split('=')[1].strip()
            elif 'VORA_PASSWORD' in line:
                restored_tenant['default_tenant_pwd'] = line.split('=')[1].strip()
    return restored_tenant

def get_backup_restore_failure_detail(jobs):
    backup_validation_suc = True
    restore_validation_suc = True
    failure_message=''
    for job in jobs:
        if 'validation_test_backup' in job['name'] and job['state'] != 'finished':
            backup_validation_suc = False
        if 'validation_test_restore' in job['name'] and job['state'] != 'finished':
            restore_validation_suc = False
    if backup_validation_suc and restore_validation_suc:
        failure_message = '\n'
    elif backup_validation_suc and not restore_validation_suc:
        failure_message = 'Failed reason: There is *error in restoration process*.\n'
    elif not backup_validation_suc and restore_validation_suc:
        failure_message = 'Failed reason: *Sporadic issue*.\n'
    else:
        failure_message = 'Failed reason: There is *error in test framework content*.\n'
    return failure_message

def sendSlackMsg(job):
    base_versions = ''
    vora_version = ''
    url = ''
    creation_job_url = ''
    current_job_url = ''
    cluster_name = ''
    endpoint = ''
    default_tenant = ''
    default_tenant_password = ''
    system_tenant = ''
    system_tenant_password = ''
    use_for = 'MILESTONE_VALIDATION_upgrade'
    platform = ''
    if 'USE_FOR' in os.environ:
        use_for = os.environ['USE_FOR']

    if 'BASE_BDH_VERSIONS' in os.environ:
        base_versions = os.environ['BASE_BDH_VERSIONS']

    if "VORA_VERSION" in os.environ:
        vora_version = os.environ['VORA_VERSION']
    elif "RELEASEPACK_VERSION" in os.environ:
        vora_version = os.environ['RELEASEPACK_VERSION']

    if "K8S_CLUSTER_NAME" in os.environ:
        cluster_name = os.environ['K8S_CLUSTER_NAME']

    if 'VSYSTEM_ENDPOINT' in os.environ:
        endpoint = os.environ['VSYSTEM_ENDPOINT']

    if 'INFRABOX_BUILD_URL' in os.environ:
        url = updateURL(os.environ['INFRABOX_BUILD_URL'])

    if "VORA_TENANT" in os.environ:
        default_tenant = os.environ['VORA_TENANT']

    if 'VORA_PASSWORD' in os.environ:
        default_tenant_password = os.environ['VORA_PASSWORD']

    system_tenant = os.getenv('VORA_SYSTEM_TENANT', 'system')

    if 'VORA_SYSTEM_TENANT_PASSWORD' in os.environ:
        system_tenant_password = os.environ['VORA_SYSTEM_TENANT_PASSWORD']

    if 'PROVISION_PLATFORM' in os.environ:
        platform = os.environ['PROVISION_PLATFORM']
    channel = 'di-upgrade-validation'
    job_api_url = ''
    base_versions_list = []

    if "INFRABOX_JOB_API_URL" in os.environ:
        job_api_url = os.environ['INFRABOX_JOB_API_URL']

    msg = ''
    jobs = job.get('parent_jobs', [])
    if use_for == 'MILESTONE_VALIDATION_upgrade':
        base_versions_list = base_versions.split(',')
        msg = 'Upgrade validation was *<test_reulst>* on `{}`. upgrade from `{}` to `{}`, please refer to: <{}| build url>.\n'.format(platform, base_versions, vora_version, url)
    else:
        channel = 'di-backup-restore-validation'
        msg = 'Backup/restore validation was *<test_reulst>* with DI version `{}` on `{}`, please refer to: <{}| build url>.\n'.format(vora_version, platform, url)
        msg += get_backup_restore_failure_detail(jobs)

    success = True
    cluster_deleted = False
    creation_job_info = get_creation_job_info(jobs)
    if 'job_url'in creation_job_info and creation_job_info['job_url'] != "" and url != "":
        creation_job_url = url + '/job/' + creation_job_info['job_url']
    creation_info = ''
    cluster_info = ''
    system_info = ''
    failed_jobs_info = ''
    restored_cluster_info = ''
    restored_tenant_info = ''
    if creation_job_info['state'] != 'finished':
        create_with_version = base_versions_list[0] if len(base_versions_list) > 0 else vora_version
        creation_info += '\n- Cluster creaton failed:\
        \n>`{}` failed, please refer to <{}| job url>.\
        \n>Try to install with DI version: `{}` failed.'.format(creation_job_info['name'], creation_job_url, create_with_version)
        success = False
    else:
        validaiton_job_pattern = '_test_|_backup_|_restore_'
        for j in jobs:
            if cluster_info == '':
                admin_conf = get_admin_conf(job_api_url, creation_job_info['id'] )
                cluster_info += '\n- Cluster infomation:\
                \n>Cluster creation job: <{}|url>\
                \n>Cluster name: `{}`\
                \n>Download kube config: <{}|admin.conf>\n'.format(creation_job_url, cluster_name, admin_conf)
            if system_info == '':
                if platform.lower().startswith('dhaas') or ('_backup_' in j['name'] and j['state'] =='finished'):
                    system_info += '\n- Tenant infomation:\
                    \n>default_tenant: [{}]/`{}`\
                    \n>system_tenant: [{}]/`{}`\
                    \n>endpoint: [{}]\n'.format( default_tenant, default_tenant_password, system_tenant, system_tenant_password, endpoint)
            current_job_url = '{}/job/{}'.format(url, j['raw_name'].replace('/','%2F'))

            if j['name'].startswith('create_restored_cluster_') and j['state'] == 'finished':
                if restored_cluster_info == '':
                    restored_cluster_info = get_restored_cluster_info(j, job_api_url, current_job_url)

            if '_restore_' in j['name'] and j['state'] =='finished':
                if j['name'].endswith('_dhaas_aws') and restored_cluster_info == '':
                    restored_cluster_info = get_restored_cluster_info(j, job_api_url, current_job_url)
                restored_tenant = get_restored_tenant_info(j['name'])
                if restored_tenant_info == '' and restored_tenant is not None:
                    restored_tenant_info += '\n- Restored tenant infomation:\
                    \n>default_tenant: [{}]/`{}`\
                    \n>system_tenant: [{}]/`{}`\
                    \n>endpoint: [{}]\n'.format( restored_tenant['default_tenant'], restored_tenant['default_tenant_pwd'], restored_tenant['system_tenant'], restored_tenant['system_tenant_pwd'], restored_tenant['endpoint'])

            if (j['state'] == 'failure' or j['state'] == 'unstable') and re.search(validaiton_job_pattern, j['name']):
                if failed_jobs_info == '':
                    failed_jobs_info = "\n- Failed validation jobs:"
                if 'system_upgrade' in j['name']:
                    upgrade_from, upgrade_to = get_ugrade_info(j['name'], base_versions_list, vora_version)
                    failed_jobs_info += '\n>`{}` failed, upgrade from `{}` to `{}`, please check <{}|job url>'.format(j['name'], upgrade_from, upgrade_to, current_job_url)
                else:
                    failed_jobs_info += '\n>`{}` failed, please check <{}|job url>.'.format(j['name'], current_job_url)
                success = False

            if "_deletion_" in j['name'] and j['state'] == "finished":
                cluster_deleted = True
    icon = ':gh-check-passed:'
    if success and cluster_deleted:
        msg = msg.replace('<test_reulst>', 'successful')
    else:
        icon = ':gh-check-failed:'
        msg = msg.replace('<test_reulst>', 'failed')
        msg += creation_info + cluster_info + system_info + restored_cluster_info + restored_tenant_info + failed_jobs_info
    slack_message(icon + msg, channel)


def compare_job_cost_time(job_name, job_cost_time, normal_job_costs):
    cost_info = ""

    for key, normal_job_cost in normal_job_costs.items():
        normal_job_cost = timedelta(minutes=int(normal_job_cost))
        if job_name == key:
            if job_cost_time > normal_job_cost:
                cost_info = "[ " + job_name + " ] time cost: " + str(job_cost_time) + \
                    "(normal time cost: " + str(normal_job_cost) + ")\n"
            else:
                cost_info = "[ " + job_name + " ]" + " time cost : NORMAL\n"

    return cost_info


def need_send_alert_email(build_cost_time, build_type, normal_build_costs):
    result = False

    for key, normal_build_cost in normal_build_costs.items():
        normal_build_cost = timedelta(minutes=int(normal_build_cost))
        if build_type == key:
            if build_cost_time > normal_build_cost:
                result = True

    return result

def sendBuildDurationSummaryToRestAPI(jsonObj):
    url = "https://api.dashboard.datahub.only.sap:30711/api/v1/trd/build/durationSummary"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/json')
    jsonContent = json.dumps(jsonObj)
    print (jsonContent)
    response = urllib2.urlopen(req, jsonContent, context=ctx)
    responseContent = response.read()
    print ("sendBuildDurationSummaryToRestAPI response: " + responseContent)
    if response.getCode() != 200:
        raise Exception("Unexpected response!")


def generateBuildDurationSummary(actual_time, base_time, build_id):
    jsonObj = {}
    jsonObj['build_duration_summary'] = {}
    jsonObj['build_duration_summary']['actual_time'] = actual_time
    jsonObj['build_duration_summary']['base_time'] = base_time
    jsonObj['environment'] = {}
    jsonObj['environment']['BUILD_ID'] = build_id
    if 'GERRIT_CHANGE_BRANCH' in os.environ:
        jsonObj['environment']['GERRIT_CHANGE_BRANCH'] = os.environ['GERRIT_CHANGE_BRANCH']
    if 'GERRIT_PROJECT' in os.environ:
        jsonObj['environment']['GERRIT_PROJECT'] = os.environ['GERRIT_PROJECT']
    jsonObj['environment']['USE_FOR'] = "PUSH_VALIDATION"
    return jsonObj

def build_time_alert(infrabox_build_id, infrabox_build_url):
    with open('/infrabox/job.json', 'r') as f:
        job_data = json.load(f)

    with open('/project/normal_job_time_cost.json', 'r') as f:
        time_cost = json.load(f)
    normal_job_costs = time_cost["job_costs"]
    normal_build_costs = time_cost["build_costs"]

    build_start_time = parser.parse("9999-12-30 00:00:00+00:00")
    build_end_time = parser.parse("0001-01-01 00:00:00+00:00")
    cost_info = "\n"
    build_type = "normal"
    has_restarted = False

    for job in job_data['parent_jobs']:

        job_name = job['name'].split('/')[-1]
        if "." in job_name:
            job_name = job_name.split('.')[0]
            has_restarted = True

        if "hanalite_dqp_test" in job_name:
            build_type = "update_reposity"

        if "update_test" in job_name:
            build_type = "upgrade_test"

        job_start_date = job['start_date']
        job_end_date = job['end_date']
        if job_start_date == 'None' or job_end_date == 'None':
            print ("Skip the job %s as time info is None!" % job_name)
            continue
        job_start_date = parser.parse(job_start_date)
        job_end_date = parser.parse(job_end_date)
        job_cost_time = job_end_date - job_start_date

        if job_start_date < build_start_time:
            build_start_time = job_start_date

        if job_end_date > build_end_time:
            build_end_time = job_end_date

        cost_info += compare_job_cost_time(job_name, job_cost_time, normal_job_costs)


    if build_end_time > build_start_time:
        build_cost_time = build_end_time - build_start_time

    if need_send_alert_email(build_cost_time, build_type, normal_build_costs):

        cost_info += "\nBuild Cost Time : " + str(build_cost_time) + "\n"
        cost_info += "INFRABOX_BUILD_URL : " + infrabox_build_url + "\n"
        if has_restarted:
            cost_info += "Job in this Build has been restarted!"

        mail = SendEmail('mail.sap.corp')
        sub_title = "[Build Time Cost Alert] Build ID : " + infrabox_build_id
        receivers = ['edward.wang@sap.com', 'max.zhang@sap.com', 'jing.li08@sap.com']
        print (receivers)
        print ("Cost Info:\n" + cost_info)
        base_time = timedelta(minutes=int(normal_build_costs[build_type]))
        jsonObj = generateBuildDurationSummary(str(build_cost_time), str(base_time), infrabox_build_id)

        try:
            mail.sendTxtMail(receivers, sub_title, cost_info, subtype='plain')
        except Exception as e:
            print ("Send Email Unsuccessfully! The error message is: " + str(e))
        print ("Send Email Successfully!")

        try:
            sendBuildDurationSummaryToRestAPI(jsonObj)
        except Exception as e:
            print ("Post BuildDurationSummaryRestAPI Unsuccessfully! The error message is: " + str(e))
        print ("Post BuildDurationSummaryRestAPI successfully")

    else:
        print ("No Need to Alert!")
        print ("Cost Info:\n" + cost_info)

def get_PR_title_label(PR_FULL_NAME, PR_NO):
    github_url = 'https://github.wdf.sap.corp/api/v3/repos/' + PR_FULL_NAME + '/pulls/' + PR_NO
    print('github_urli is ' + github_url)
    velobot_token = os.getenv("VELOBOT_TOKEN",'')
    auth_values = ('velobot', velobot_token)
    print(auth_values)
    headers = {'x-requested-with':'Fetch', 'Content-Type': 'application/json'}
    try:
        ret = requests.get(github_url, auth=auth_values, headers=headers, verify=False)
        response_json = json.loads(ret.text)
        print(response_json)
        title = response_json['title']
        title_sub = 'chore: validate components update on landscape'
        if title.find(title_sub) != -1:
            title = title[len(title_sub)+1:]
        labels_json = response_json['labels']
        if labels_json:
            labels = ','.join(label['name'] for label in labels_json)
        else:
            labels = ''
        return title, labels

    except Exception as e:
        print(str(e))
        return '',''
