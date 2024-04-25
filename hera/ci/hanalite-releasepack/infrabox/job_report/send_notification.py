#!/usr/bin/env python
import os
import os.path
import json
import traceback
import sys
from send_job_report import generateJsonObject
from send_job_report import sendReportToRestAPI
from send_job_report import sendDefaultReceiverJobReport
from send_job_report import sendComponentReceiverJobReport
from send_job_report import sendPlatformReceiverJobReport
from send_job_report import getJobJsonFromRestAPI
from send_job_report import sendReportToRestAPIErrorEmail
from send_job_report import sendSlackMsg
from send_job_report import filterJobsName
from send_job_report import build_time_alert

if __name__ == "__main__":
    subTitle = ""
    sendDefaultAlways = False
    commitLog = "/infrabox/inputs/build_copy_files/recent_commit_log"
    voraVersion = None
    useConfigFile = False
    defaultReceivers = []
    componentReceivers = None
    platformReceivers = None
    voraMilestonePath = None
    componentVersions = None

    sendEmail = False
    sendReport = False
    if "USE_FOR" in os.environ:
        subTitle = os.environ['USE_FOR']

    if subTitle == "":
        print ("## No USE_FOR setting in env, skip job_report.")
        sys.exit()

    if "VORA_VERSION" in os.environ:
        voraVersion = os.environ['VORA_VERSION']
    elif "DIS_VERSION" in os.environ:
        voraVersion = os.environ['DIS_VERSION']

    if "VORA_MILESTONE_PATH" in os.environ:
        voraMilestonePath = os.environ['VORA_MILESTONE_PATH']

    if "ALL_COMPONENTS_VERSIONS" in os.environ:
        if os.environ['USE_FOR'] == "DIS_VALIDATION_pr":
            os.environ['ALL_COMPONENTS_VERSIONS'] = (os.environ['ALL_COMPONENTS_VERSIONS']).replace("\'", '\"')
        componentVersions = json.loads(os.environ['ALL_COMPONENTS_VERSIONS'])
        print ("## all components versions in python:")
        print (json.dumps(componentVersions, indent=4, sort_keys=True))

    if "SLC_BRIDGE_BASE_VERSION" in os.environ:
        slcbVersion = os.environ['SLC_BRIDGE_BASE_VERSION']

    job = None
    manuallyBuildNumber = os.environ.get('MANUALLY_BUILD_NUMBER', '')
    manuallyRestartCount = os.environ.get('MANUALLY_RESTART_COUNT', '')
    if manuallyBuildNumber:
        restAPIHost = os.environ.get('RESTAPI_HOST', '')
        restAPIPort = os.environ.get('RESTAPI_PORT', '')
        restAPIEmailPath = os.environ.get('RESTAPI_EMAIL_PATH', '')
        if not restAPIHost:
            print ('## REST API host is not set, job.json will be set to None.')

        job = getJobJsonFromRestAPI(restAPIHost, restAPIPort, restAPIEmailPath, manuallyBuildNumber, manuallyRestartCount, subTitle, componentVersions)
        sendEmail = True
    else:
        job = json.load(open('/infrabox/job.json', 'r'))
        job = filterJobsName(job)
    if job is None:
        print ("Job.json is none, exit!")
        sys.exit()   

    projectName = job['project']['name']

    if subTitle == "PUSH_VALIDATION" and projectName in [ "hanalite-releasepack", "hanalite" ]:
        sendEmail = True
        sendReport = True
        infrabox_build_id = os.environ.get('INFRABOX_BUILD_NUMBER', '') + "." + os.environ.get('INFRABOX_BUILD_RESTART_COUNTER', '')
        infrabox_build_url = os.environ.get('INFRABOX_BUILD_URL', '')
        try:
            build_time_alert(infrabox_build_id, infrabox_build_url)
        except Exception as e:
            print ("## Build Time Alert Fail! The error message is: " + str(e))

    if subTitle == "MILESTONE_VALIDATION" and projectName in ['milestone_validation', 'milestone-validation']:
        sendEmail = True
        sendReport = True

    if subTitle == "MILESTONE_VALIDATION_preview" and projectName in ['milestone_validation', 'milestone-validation']:
        sendEmail = False
        sendReport = True
    
    if subTitle == "MILESTONE_VALIDATION_e2e" and projectName == "e2e-validation":
        sendEmail = False
        sendReport = True

    if subTitle == "SLCB_VALIDATION" and projectName == "slcb-di-validation":
        sendEmail = True
        
    if subTitle == "COMPONENT_IMAGE_VALIDATION" and projectName == "test-image-validation":
        sendEmail = True
        sendReport = True
        
    if subTitle == "MILESTONE_VALIDATION_backup" and projectName == "milestone_validation_backup":
        sendEmail = True
        sendReport = True
        sendSlackMsg(job)

    if subTitle == "NIGHTLY_VALIDATION_debug" and projectName in [ "Hananlite-Releasepack-nightly-dev", "Hananlite-Releasepack-nightly-dev-master" ]:
        sendEmail = True
        sendReport = True

    if subTitle == "NIGHTLY_VALIDATION" and projectName in [ "Hanalite-releasepack_Continues_validation", "Hananlite-releasepack-nightly-stable" ]:
        sendReport = True
        if manuallyBuildNumber:
            sendReport = False

    if subTitle in [ "DEMAND_VALIDATION", "PUSH_VALIDATION_bdh-infra-tools" ]:
        sendEmail = True

    if subTitle == "MILESTONE_VALIDATION_upgrade" and  projectName == "upgrade-validation":
        sendEmail = True
        sendReport = True
        sendSlackMsg(job)
    if subTitle == "AUTO_ENV":
        sendEmail = True

    if subTitle == "DIS_VALIDATION_pr" and projectName in ['dis-release']:
        sendEmail = True
        sendReport = True

    sendEmailSuccess = True
    if sendEmail:
        emailJson = json.load(open('config_' + subTitle  + '.json', 'r'))

        if 'default_receivers' in emailJson and len(emailJson['default_receivers']) > 0:
            defaultReceivers = emailJson['default_receivers'].split(',')

        if 'component_receivers' in emailJson:
            componentReceivers = emailJson['component_receivers']

        if 'platform_receivers' in emailJson:
            platformReceivers = emailJson['platform_receivers']

        if "GERRIT_CHANGE_OWNER_EMAIL" in os.environ:
            defaultReceivers.append(os.environ['GERRIT_CHANGE_OWNER_EMAIL'])

        if "DEFAULT_RECEIVERS" in os.environ:
            defaultReceivers.extend(os.environ['DEFAULT_RECEIVERS'].split(','))

        if subTitle in [ "NIGHTLY_VALIDATION", "DEMAND_VALIDATION", "MILESTONE_VALIDATION", "MILESTONE_VALIDATION_upgrade", "SLCB_VALIDATION","AUTO_ENV", "DIS_VALIDATION_pr" ]:
            sendDefaultAlways = True

        gerritChangeURL = None
        if "GERRIT_CHANGE_URL" in os.environ:
            gerritChangeURL = os.environ['GERRIT_CHANGE_URL']

        dashboardURL = None
        if "DASHBOARD_URL" in os.environ:
            dashboardURL = os.environ['DASHBOARD_URL']
            if manuallyBuildNumber:
                dashboardURL = dashboardURL + manuallyBuildNumber + '.' + manuallyRestartCount

        if not os.path.isfile(commitLog):
            commitLog = None

        if job.get('local', False):
            print ('Local job, not sending message')
        else:
            try:
                if subTitle == "AUTO_ENV":
                    K8S_ADM_CFG_PATH_OUTPUT = os.environ['K8S_ADM_CFG_PATH_OUTPUT']
                    commitLog = [K8S_ADM_CFG_PATH_OUTPUT]
                sendDefaultReceiverJobReport(job, subTitle, sendDefaultAlways, defaultReceivers, gerritChangeURL, commitLog, voraVersion, dashboardURL, voraMilestonePath)
            except Exception:
                print ("## Error when sending email to default receivers:")
                traceback.print_exc(file=sys.stdout)
                sendEmailSuccess = False
            try:
                sendComponentReceiverJobReport(job, subTitle, componentReceivers, gerritChangeURL, commitLog, voraVersion, dashboardURL, voraMilestonePath)
            except Exception:
                print ("## Error when sending email to component receivers:")
                traceback.print_exc(file=sys.stdout)
                sendEmailSuccess = False
            try:
                sendPlatformReceiverJobReport(job, subTitle, platformReceivers, gerritChangeURL, commitLog, voraVersion, dashboardURL, voraMilestonePath)
            except Exception:
                print ("## Error when sending email to platform receivers:")
                traceback.print_exc(file=sys.stdout)
                sendEmailSuccess = False

    sendReportSuccess = True
    if sendReport:
        restAPIHost = os.environ.get('RESTAPI_HOST', '')
        restAPIPort = os.environ.get('RESTAPI_PORT', '')
        restAPIPath = os.environ.get('RESTAPI_PATH', '')
        if not restAPIHost:
            print ('## REST API host is not set, request is not sent.')
            sendReportToRestAPIErrorEmail('REST API host is not set, request is not sent.')
            sendReportSuccess = False

        jsonObj = None

        try:
            jsonObj = generateJsonObject(job, '/infrabox/inputs/build_copy_files/recent_commit_log.json', voraVersion, subTitle, voraMilestonePath, componentVersions)
        except Exception:
            print ('## Error when generateing job josn, request is not sent.')
            sendReportToRestAPIErrorEmail('Error when generateing job json, request is not sent.')
            traceback.print_exc(file=sys.stdout)
            sendReportSuccess = False

        # if build/k8s_creation/install fails, print data instead of insert to TRD
        #if projectName in ["Hanalite-releasepack_Continues_validation", "Hananlite-releasepack-nightly-stable", "milestone_validation"] and setupClusterSucceed(job, subTitle) is False:
        #    print "## As cluster setup(build/create/install) fails, will not insert report to TRD automatically, please check for failure!"
        #    sendReportSuccess = False
        #    print "If necessary, insert to TRD manually:"
        #    if not restAPIPort:
        #        url = restAPIHost + restAPIPath
        #    else:
        #        url = restAPIHost + ':' + restAPIPort + restAPIPath
        #    print "restAPI url: ", url
        #    sendReportToInstallJobErrorEmail('As cluster setup(build/create/install) fails, will not insert report to TRD automatically, please check for failure!')

        if jsonObj is not None:
            print ("Saving the request json to Archive")
            with open('/infrabox/upload/archive/request_json_data.json', 'w') as outfile:
                json.dump(jsonObj, outfile)

        if sendReportSuccess:
            try:
                sendReportToRestAPI(restAPIHost, restAPIPort, restAPIPath, jsonObj)
            except Exception:
                print ('## error when sending report:')
                sendReportToRestAPIErrorEmail('Error when sending report.')
                traceback.print_exc(file=sys.stdout)
                sendReportSuccess = False

    #TODO: enable this when it's more stable # pylint:disable=fixme
    #Only if send report to trd/insert fail, make report job fail (exclude push validation)
    if not sendReportSuccess and not (subTitle == "PUSH_VALIDATION" and projectName in [ "hanalite-releasepack", "hanalite" ]):
        exit(1) # pylint:disable=bad-option-value,consider-using-sys-exit

