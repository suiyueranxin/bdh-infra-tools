#!/usr/bin/env python
import os
import os.path
import json
import datetime
import urllib2
import ssl

def generateJsonObject(taskName):
    job = json.load(open('/infrabox/job.json', 'r'))
    jobs = job.get('parent_jobs', [])
    if len(jobs) == 0:
        return None
    jsonObj = {}
    jsonObj['taskname'] = taskName
    jsonObj['timestamp'] = str(datetime.datetime.now())
    jsonObj['status'] = []

    for j in jobs:
        jsonObj['status'].append({'step_name': j['name'], 'status': j['state']})

    return jsonObj

def sendJsonObject(restAPIHost, restAPIPort, restAPIPath, jsonObj):
    if not restAPIPort:
        url = restAPIHost + restAPIPath
    else:
        url = restAPIHost + ':' + restAPIPort + restAPIPath

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/json')
    jsonContent = json.dumps(jsonObj)
    print jsonContent

if __name__ == "__main__":
    taskName = os.environ.get('TASKNAME', '')
    if not taskName:
        print '## Error: no task name, process callback is not sent.'
        exit(1)

    restAPIHost = os.environ.get('RESTAPI_HOST', '')
    restAPIPort = os.environ.get('RESTAPI_PORT', '')
    restAPIPath = os.environ.get('RESTAPI_PATH', '')
    if not restAPIHost:
        print '## REST API host is not set, process callback is not sent.'
        exit(1)
 
    jsonObj = generateJsonObject(taskName)
    if jsonObj is None:
        print '## Error: No parent jobs, process callback is not sent.'
        exit(1)

    sendJsonObject(restAPIHost, restAPIPort, restAPIPath, jsonObj)
