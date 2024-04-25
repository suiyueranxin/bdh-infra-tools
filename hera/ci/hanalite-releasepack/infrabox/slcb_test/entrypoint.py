import os
import sys
import json
import re
def fiter_platforms(jobs):
    full_platform = os.environ.get("FULL_PLATFORM", "GKE,EKS,AZURE-AKS").lower()
    full_platform_pattern = full_platform.replace(',','|').replace('azure-aks','aks')
    new_jobs = []
    for job in jobs:
        if job['name'].startswith('build'):
            new_jobs.append(job)
        else:
            if re.search(full_platform_pattern, job['name']):
                new_jobs.append(job)
    return new_jobs

def main():
    infrabox_json = None
    with open('/project/slcb_validation.json','r')as fp:
        infrabox_json = json.load(fp)
    if infrabox_json is None:
        return 
    slcb_image = os.environ.get("SLCB_BINARY_IMAGE", "di-dev-cicd-v2.int.repositories.cloud.sap/slcb/com.sap.sl.cbpod/slcbexe")
    slcb_tag = os.environ.get("CUSOTOMIZED_SLCB_TAG", "1.1.73")
    infrabox_json["jobs"] = fiter_platforms(infrabox_json["jobs"])
    for job in infrabox_json["jobs"]:
        if job["name"].startswith('install') or job["name"].startswith('uninstall') or job["name"].startswith('build'):
            if "environment" not in job:
                job["environment"] = {}  
            dev_config = "export SLCB_BINARY_IMAGE_SOURCE_CUSTOM=" + slcb_image.split('/')[0] + "/"
            job["environment"]["SLCB_BINARY_IMAGE"] = slcb_image
            job["environment"]["DEV_CONFIG_FILE_CONTENT"] = dev_config
            job["environment"]["CUSOTOMIZED_SLCB_TAG"] = slcb_tag
        if 'job_report' in job["name"]:
            job["environment"]["SLCB_BINARY_IMAGE"] = slcb_tag
    with open('/infrabox/output/infrabox.json', 'w') as txt:
        json.dump(infrabox_json, txt)   
        
if __name__ == '__main__':
    main()