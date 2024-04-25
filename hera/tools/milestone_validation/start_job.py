#!/usr/bin/python
import os
import sys
import json
import subprocess
from subprocess import call
import datetime
import shutil

provision_platform_dict = {
    "GKE": "GKE",
    "MONSOON": "MONSOON",
    "AWS-EKS": "AWS-EKS",
    "EKS": "AWS-EKS",
    "AWS": "AWS-EKS",
    "GARDENER-AWS": "GARDENER-AWS",
    "AWS-GARDENER": "GARDENER-AWS",
    "AKS": "AZURE-AKS",
    "AZURE-AKS": "AZURE-AKS",
    "DHAAS-AWS": "DHAAS-AWS"
}

test_platform_dict = {
    "GKE": "_gke",
    "MONSOON": "_monsoon",
    "EKS": "_eks",
    "AWS-EKS": "_eks",
    "AWS": "_eks",
    "GARDENER-AWS": "_gardener_aws",
    "AWS-GARDENER": "_gardener_aws",
    "AKS": "_aks",
    "AZURE-AKS": "_aks",
    "DHAAS-AWS": "_dhaas_aws"
}



def start_milestone_backup_build(base_folder, version, repo_url, branch_name=None):
    if branch_name is None:
        branch_name = ""
    upgrade_file = os.path.join(base_folder, "start_job_milestone_backup.sh")
    result = call([upgrade_file, version, repo_url, branch_name])
    if result != 0:
        print("Milestone Backup/Restore Test Create Fail!")
    return
