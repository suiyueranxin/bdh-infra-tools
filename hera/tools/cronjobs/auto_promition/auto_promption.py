#!/usr/bin/env python
import os
import json
import urllib2
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

class SendEmail(object):
    def __init__(self, host):
        server = smtplib.SMTP(host, 587)
        self._server = server
        self._me ="sap_bdh_infra@sap.com"
        mail_pwd="Sapvora123"
        mail_usr="bdh-infra-notifications"
        #server.set_debuglevel(1)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(mail_usr, mail_pwd)

    def sendTxtMail(self, to_list, sub, content, subtype='html'):
    	#subtype could be plain or html
        msg = MIMEText(content, _subtype=subtype, _charset='utf-8')  
        msg['Subject'] = sub  
        msg['From'] = self._me  
        msg['To'] = ",".join(to_list)  
        try:
            self._server.sendmail(self._me, to_list, msg.as_string())   
            return True  
        except Exception, e:  
            print str(e)  
            return False
    
    def sendAttachMail(self, to_list, sub, content, attach_file_list, subtype='html'):
       
        msg = MIMEMultipart()  
    
        for attach_file in attach_file_list:
            filename = os.path.basename(attach_file) 
            att = MIMEText(open(attach_file,'rb').read(), 'base64', 'utf-8')
            att["Content-Type"] = 'application/octet-stream'
            att["Content-Disposition"] = "attachment; filename=" + filename
            msg.attach(att)
    
        msg.attach(MIMEText(content, _subtype=subtype, _charset='utf-8'))
        
        msg['Subject'] = sub  
        msg['From'] = self._me
        msg['To'] = ",".join(to_list)
         
        try:
            self._server.sendmail(self._me, to_list, msg.as_string())   
            return True  
        except Exception, e:  
            print str(e)  
            return False

    def __del__(self):
        if self._server:
            self._server.quit()
            self._server.close()

def sendRequest(restAPIHost, restAPIPort, restAPIPath, jsonObj):
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
    response = urllib2.urlopen(req, jsonContent, context=ctx)
    #print response.getcode()
    if response.getcode() not in [200, 201]:
        raise Exception("Unexpected response!")
    responseContent = response.read()
    #print "sendReportToRestAPI response: " + responseContent
    data = json.loads(responseContent)
    return data




RESTAPI_HOST = "https://mo-09337e89c.mo.sap.corp"
RESTAPI_PORT = "50030"
RESTAPI_PATH = "/api/v1/trd/job/trend"


def getLatestBuildId(result):
    latest=1.1
    for item in result["dataList"]:
        if "sort_id_list" in item and len(item["sort_id_list"]) >= 1:
            curBuildId=item["sort_id_list"][0]
            latest = curBuildId if curBuildId> latest else latest
    return latest

jsonObj = {"environment": {"GERRIT_CHANGE_BRANCH": "master","GERRIT_PROJECT": "hanalite-releasepack","USE_FOR": "NIGHTLY_VALIDATION_debug"}}
result = sendRequest(RESTAPI_HOST, RESTAPI_PORT, RESTAPI_PATH, jsonObj)

latestBuildId = int(str(getLatestBuildId(result)).split('.')[0])

latestPassed=[]
for item in result["dataList"]:
    if "job_name" not in item or "_test_" not in item["job_name"]:
        continue
    if "sort_id_list" not in item or len(item["sort_id_list"]) < 1 or int(str(item["sort_id_list"][0]).split('.')[0]) < latestBuildId:
        continue
    if "job_state_list" not in item or len(item["job_state_list"]) < 3:
        continue
    if item["job_state_list"][0] == "finished" and item["job_state_list"][1] == "finished" and item["job_state_list"][2] == "finished":
        latestPassed.append(item["job_name"])

if latestPassed != []:
    receivers = ["kang.shi01@sap.com","max.zhang@sap.com","phoebe.wang@sap.com"]
    mail = SendEmail('mail.sap.corp')
    title="Test jobs that can be prompt to milestone validation"
    Report = """\
        <html>
        <head></head>
        <body>
            <p>Dear colleagues,
            <p>Following jobs are successfully run in 3 nightly validation builds continuesly, please prompt to milestone validation:</p>
            <p>%s
            <p>Best regards, 
            <p>BDH Infrastructure Xi&#39an Team</p>
        </body>
        </html>
        """ % '<p>'.join(latestPassed)
    mail.sendTxtMail(receivers,title,Report)
