#!/usr/bin/env python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os

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
            try: 
                att = MIMEText(open(attach_file,'rb').read(), 'base64', 'utf-8')
                att["Content-Type"] = 'application/octet-stream'
                att["Content-Disposition"] = "attachment; filename=" + filename
                msg.attach(att)
            except IOError:
                print("File ("+attach_file+") not accessible")

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
