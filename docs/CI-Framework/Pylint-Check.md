# Pylint Check

## How to pylint

1.install pylint
```
pip install pylint
```

2.pylint check
* Only check one python file, execute this command:
```
pylint python_name.py
``` 
* Check all bdh-infra-tools python files, execute this script */bdh-infra-tools/pylint.sh* like this, the result will store in pylint_check.log:
```
./pylint.sh > pylint_check.log
```
Note: *pylint.sh* ignore some disable rules maked in the */bdh-infra-tools/.pylintrc*.

## How to correct

1.Start Pylint: ./hera/ci/hanalite-releasepack/infrabox/multiple_step_upgrade/entrypoint.py

`W:  2, 0: Unused import sys (unused-import)`  
rm this import  
```
import sys
```

2.Start Pylint: hera/ci/hanalite-releasepack/infrabox/job_report/send_job_report.py 

`W:  8, 0: Wildcard import slacklib (wildcard-import)`

change  
```
from slacklib import *
```  
to  
```
from slacklib import slack_message
```

3.Start Pylint: ./common/ansible/library/ambari.py  
`C: 11, 0: Old-style class defined. (old-style-class)`

Change  
```
class Log:
```  
to  
```
class Log(object):
```

4.Start Pylint: common/ansible/roles/vora/vora-kubernetes-install-cloud/files/save_install_cmd.py  
`W: 45, 4: No exception type(s) specified (bare-except)`  
change
```
    except:
        print "Output the install command failed!"
```
to
```
    except Exception as e:
        print "Output the install command failed! The error message is: " + e.message

```

5.Start Pylint: ./common/ansible/tools/bdh_health_check.py  
`R:180, 7: Comparison to literal (literal-comparison)`

Change  
```
if os.getenv("VORA_TENANT", "") is not "" \
```  
to  
```
if os.getenv("VORA_TENANT", "") != "" \
```  

6.Start Pylint: ./hera/ci/hanalite-releasepack/infrabox/job_report/send_job_report.py
`C:139, 7: Comparison to None should be 'expr is None' (singleton-comparison)`  
change  
```
if commitLog == None:
```  
to  
```
if commitLog is None:
```  

7.Start Pylint: ./hera/ci/hanalite-releasepack/infrabox/job_report/send_notification.py  
`C:216, 7: Comparison to False should be 'not expr' or 'expr is False' (singleton-comparison)`  
change  
```
 if sendReportSuccess == False and not (subTitle == "PUSH_VALIDATION" and projectName in [ "hanalite-releasepack", "hanalite" ]):
```
to
```
 if not sendReportSuccess and not (subTitle == "PUSH_VALIDATION" and projectName in [ "hanalite-releasepack", "hanalite" ]):
```

8.Start Pylint: ./common/ansible/tools/get_latest_milestone.py  
`W: 64, 8: Redefining built-in 'list' (redefined-builtin)
W: 66,12: Redefining built-in 'str' (redefined-builtin)`

change  
```
        list = data['dataList'];
        for each in list:
            str = each['prod_version'].encode("utf-8")
```  
to        
```
        list_data = data['dataList']
        for each in list_data:
            prod_str = each['prod_version'].encode("utf-8")
```  

9.Start Pylint: ./common/script/python/send_mail.py            
`W: 22, 0: Found indentation with tabs instead of spaces (mixed-indentation)`

change  
```
        msg = MIMEText(content, _subtype=subtype, _charset='utf-8')
```  
to  
```
        msg = MIMEText(content, _subtype=subtype, _charset='utf-8')
```  

10.Start Pylint: ./common/ansible/filter_plugins/string.py  
`C: 36, 0: Trailing newlines (trailing-newlines)`

rm the last empty line

11.Start Pylint: ./hera/tools/update_test_plan/update_test_plan.py  
`E:121,16: Undefined variable 'api' (undefined-variable)`  

add api definition  
```
api = ODTEMApi()
```  

12.Start Pylint: ./hera/ci/hanalite-releasepack/infrabox/job_report/send_job_report.py  
`C:180,20: Consider iterating the dictionary directly instead of calling .keys() (consider-iterating-dictionary)`  

change  
```
for receiver in receiversDict.keys():
        success = True
        receiverJobs = []
        for component in receiversDict[receiver]:
```  
to  
```
    for receiver,componentNames in receiversDict:
        success = True
        receiverJobs = []
        for component in componentNames:
```  

13.Start Pylint: ./hera/ci/hanalite-releasepack/infrabox/job_report/send_job_report.py  
`E:730,51: Module 'os' has no 'env' member (no-member)`

change  
```
jsonObj['environment']['GERRIT_PROJECT'] = os.env['GERRIT_PROJECT']
```  
to  
```
jsonObj['environment']['GERRIT_PROJECT'] = os.environ['GERRIT_PROJECT']
```  

14.Start Pylint: common/script/python/get_email_by_I_number.py
`R:  4, 0: Either all return statements in a function should return an expression, or none of them should. (inconsistent-return-statements)`  

change  
```
if ret[0][1]['mail'][0]:
    return ret[0][1]['mail'][0]
else:
    print "Can't found email by I number , see detail info as: %s" %str(ret)
```

to  
```
if ret[0][1]['mail'][0]:
    return ret[0][1]['mail'][0]
else:
    print "Can't found email by I number , see detail info as: %s" %str(ret)
    return None
```

