#!/usr/bin python
import json
import logging
import requests
import os
logger = logging.getLogger()
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

class ODTEMApi:
    def __init__(self):
        self.base_url = os.environ.get("ODTEM_BASE_URL", "https://odtem-api.datahub.only.sap/api/v1")

    def checkCompName(self, comp_name):
        """
        check componant name is exist
        - if exist return comp_id
        - if not exist create new component
        """
        comp_url = self.base_url + "/component?prod_id=1"
        comp_output_json = requests.get(comp_url)
        comp_output = comp_output_json.json()
        comp_list = comp_output["dataList"]

        for i in range(len(comp_list)):
            if comp_name == comp_list[i]["comp_name"]:
                logger.info("comp_id: %d" %comp_list[i]["comp_id"])
                return

        logger.info("%s is not exist,insert new component name" %comp_name)
        comp_info = {
                    "prod_id":1,
                    "comp_name":comp_name
                    }
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        insert_url = self.base_url + "/component/insert"
        try:
            r = requests.post(insert_url, data=json.dumps(comp_info), headers=headers)
        except:
            raise Exception("Fail to call odtem restApi.")
        if r.status_code != 200:
            raise Exception("Fail to insert new component!")
    def getTestPlan(self, plan_name):
        """
        get testplan according to plan_name
        """
        url = self.base_url + "/test_plan?plan_name=" + plan_name
        testplan_info = requests.get(url)
        return testplan_info

    def updateTestPlan(self, test_plan):
        """
        update test_plan
        """
        # Remove elements to adapt to the format of the post
        updata_data = test_plan["dataList"][0]
        updata_data.pop("creator")
        updata_data.pop("use_for_id")
        headers = {"Accept": "application/json","Content-Type":"application/json"}
        url = self.base_url + "/test_plan/update"
        try:
            r = requests.post(url, data=json.dumps(updata_data), headers=headers)
        except :
            raise Exception("Fail to call odtem restApi.")
        if r.status_code != 200:
            raise Exception("Fail to updata testplan!")

    def findJobInTestPlan(self, job_name, test_plan_detail):
        for data in test_plan_detail["dataList"][0]["comp_test_info"]["data_list"]:
            for test in data["test"]:
                if test["case_name"] == job_name:
                    return data["comp_name"]
        return None

    def removeJobList(self, job_list, plan_name):
        """
        remove the job_list from testplan
        """
        data_input_json = self.getTestPlan(plan_name)
        data_input = data_input_json.json()
        input_datalist = data_input["dataList"][0]["comp_test_info"]["data_list"]
        for j in range(len(job_list)):
            # check Jobname is exist in testplan
            if self.findJobInTestPlan(job_list[j], data_input) == None:
                logger.warning("Can not find %s" %job_list[j])
                continue
            for i in range(len(input_datalist)):
                for k in range(len(input_datalist[i]["test"])):
                    if input_datalist[i]["test"][k]["case_name"] == job_list[j]:
                        del input_datalist[i]["test"][k]
                        logger.info("Delete the job: %s" %job_list[j])
                        break
        deleted_items = []
        for item in input_datalist:
            if len(item["test"]) == 0:
                deleted_items.append(item)

        for item in deleted_items:
            input_datalist.remove(item)

        for i in range(len(input_datalist)):
            input_datalist[i]["comp_id"] = i
        self.updateTestPlan(data_input)

    def addJobList(self, job_list, plan_name):
        """
        add job to the testplan
        """
        data_output_json = self.getTestPlan(plan_name)
        data_output = data_output_json.json()
        output_datalist = data_output["dataList"][0]["comp_test_info"]["data_list"]
        for i in range(len(job_list)):
            # check Jobname is exist in testplan
            # checkCompName(job_list[i]["comp_name"])
            if self.findJobInTestPlan(job_list[i]["case_name"], data_output) != None:
                logger.warning("%s is exist" %job_list[i]["case_name"])
                continue
            casedata = {
                "case_name" : job_list[i]["case_name"],
                "case_type" : "nightly_test"
            }
            added = False
            for k in range(len(output_datalist)):
                if (output_datalist[k]["comp_name"] == job_list[i]["comp_name"]):
                    output_datalist[k]["test"].insert(0,casedata)
                    logger.info("Add the job: %s" %job_list[i]["case_name"])
                    added = True
                    break
            if not added:
                data = {
                    "comp_id": len(output_datalist)+1,
                    "comp_name": job_list[i]["comp_name"],
                    "test": [ casedata ]
                }
                output_datalist.append(data)
        self.updateTestPlan(data_output)

