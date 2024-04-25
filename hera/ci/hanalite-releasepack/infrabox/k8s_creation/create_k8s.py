import requests
import os
import time
import logging
import timeout_decorator
import json
import re
import random
import string

check_interval = int(os.environ.get("CHECK_INTERVAL", 60))
max_error_retry_num = int(os.environ.get("MAX_ERROR_RETRY_NUM", 3))
gke_zone_quota_threshold = 45
base_url = os.environ.get("SERVER_URL", 'https://im-api.datahub.only.sap')
job_action = os.environ.get('JOB_ACTION', "Create")
upgrade_test = str(os.environ.get("UPGRADE_TEST", "no"))
bdh_base_version_file = '/infrabox/output/bdh_base_version.sh'
azure_cert_file = '/infrabox/output/azure_cert_file.sh'
provision_platform = os.environ.get("PROVISION_PLATFORM", "MONSOON")
im_central_monitor_url = os.environ.get("IM_CENTRAL_MONITOR_URL", 'https://infra-monitoring.datahub.only.sap/api/v1/components?group_id=1')

def password_generate_dhaas(password_length=30):
    """
    1. has > 30 chars
    2. has lower, upper and digits (unchanged)
    3. has at least three special chars, of which two are definitely of '?!#'
    """
    if password_length <= 0:
        raise Exception("incorrect password length!")
    special_chars = "?%!_+.#@*"
    necessary_chars = '?!#'
    possible_chars = special_chars + string.ascii_letters + string.digits
    random_password = "".join(random.sample(string.ascii_uppercase, 3)) \
    + "".join(random.sample(string.ascii_lowercase, 3)) \
    + "".join(random.sample(string.digits, 3)) \
    + "".join(random.sample(possible_chars, 21)) \
    + random.choice(necessary_chars) \
    + random.choice(necessary_chars) \
    + random.choice(special_chars)
    return random_password
random_password = password_generate_dhaas()
system_random_password = password_generate_dhaas()

env_on_premise_model = {
    "environment": {
        "PROVISION_PLATFORM": "MONSOON",
        "BUILD_NUMBER": "",
        "MONSOON_IMAGE": "RHEL7-x86_64",
        "MONSOON_MASTER_INSTANCE_TYPE": "extralarge_8_16",
        "MONSOON_WORKER_INSTANCE_TYPE": "extralarge_8_16",
        "MONSOON_REGION": "europe",
        "MONSOON_AVAILABILITY_ZONE": "rot_1",
        "NUMBER_OF_WORKERS": "3",
        "MONSOON_VOLUME_SIZE": "160",
        "K8S_VERSION": "1.16.11",
        "ENABLE_VORA_INSTALLATION": "false",
        "PERIOD": "16",
        "PERIOD_UNIT": "hour"
    }
}

env_gardener_ccloud_model = {
    "environment": {
        "PROVISION_PLATFORM": "GARDENER-CCLOUD",
        "ENABLE_AUTHENTICATION": "no",
        "ADD_INTO_FIREWALL_WHITELIST": "no",
        "BDH_ONE_NODE_INSTALLATION": "yes",
        "CCLOUD_AVAILABILITY_ZONE": "eu-de-1a",
        "CCLOUD_OS_REGION_NAME": "eu-de-1",
        "ENABLE_KANIKO": "yes",
        "ENABLE_NETWORK_POLICIES": "yes",
        "ENABLE_VORA_INSTALLATION": "false",
        "EXPOSE_TEXT_ANALYSIS": "no",
        "EXPOSE_VORA_TXC": "no",
        "EXPOSE_VSYSTEM": "yes",
        "GARDENER_CCLOUD_IMAGE_TYPE": "gardenlinux--934.8.0",
        "GARDENER_CCLOUD_WORKER_INSTANCE_TYPE": "m1.2xlarge",
        "GARDENER_PROJECT_EXT_NETWORK_SUFFIX": "external-monsoon3-05",
        "GARDENER_PROJECT_NAME": "di-cicd",
        "GARDENER_PROJECT_SECRET": "my-openstack-secret-ccloud",
        "GARDENER_SECURITY_FILE": "/gardener_api_admin.cfg",
        "INSTALL_VORA_VIA_SLCB": "true",
        "K8S_INSTALLER_WORKSPACE": "/var",
        "K8S_REMOVE_MASTER_NODE_NO_SCHEDULE_TAINT": "yes",
        "K8S_VERSION": "1.24.10",
        "MINIO_URL": "http://v2-minio.datahub.only.sap:9000",
        "NUMBER_OF_WORKERS": "3",
        "PERIOD": "24",
        "PERIOD_UNIT": "hour",
        "REGISTRY_AS_SHARED_CLUSTER": "no",
        "SKIP_VSYSTEM_ASSEMBLY": "yes",
        "TAG": "WEB",
    }
}
# n1-standard-8 8CPU 32G
env_gke_model = {
    "environment": {
        "BUILD_NUMBER": "",
        "PROVISION_PLATFORM": "GKE",
        "GCP_PROJECT_ID": "sap-p-and-i-big-data-vora",
        "GCP_ZONE": "europe-west4-b",
        "GKE_K8S_VPC": "hanalite-push-validation",
        "GCLOUD_K8S_SUBNETWORK": "dh-validation",
        "GCP_MACHINE_TYPE": "n1-standard-8",
        "GCP_IMAGE_TYPE": "cos_Containerd",
        "NUMBER_OF_WORKERS": "3",
        "GCP_NODE_VOLUME_SIZE": "50",
        "K8S_VERSION": "1.25",
        "GCLOUD_RELEASE_CHANNEL": "static",
        "ENABLE_VORA_INSTALLATION": "false",
        "NETWORK_POLICY_ENFORCEMENT": "true",
        "ADD_INTO_FIREWALL_WHITELIST":"yes",
        "PERIOD": "16",
        "PERIOD_UNIT": "hour",


    }
}
env_optional_gke_zone = [
    {
        "GCP_ZONE": "europe-west4-b",
        "GCLOUD_K8S_SUBNETWORK": "dh-validation"
    },{
        "GCP_ZONE": "europe-west3-b",
        "GCLOUD_K8S_SUBNETWORK": "dh-validation"
    },{
        "GCP_ZONE": "europe-west1-b",
        "GCLOUD_K8S_SUBNETWORK": "dh-validation"
    }
]
# Standard_D4_v2 = 8CPU 28G
env_aks_model = {
    "environment": {
        "BUILD_NUMBER": "",
        "PROVISION_PLATFORM": "AZURE-AKS",
        "NUMBER_OF_WORKERS": "3",
        "AZURE_WORKER_INSTANCE_TYPE": "Standard_D4_v2",
        "ENABLE_VORA_INSTALLATION": "false",
        "K8S_VERSION": "1.25",
        "AZURE_RESOURCE_LOCATION": "westeurope",
        "NETWORK_POLICY_ENFORCEMENT": "true",
        "ADD_INTO_FIREWALL_WHITELIST":"yes",
        "AKS_CLUSTER_NAME": "vora-k8s",
        "PERIOD": "19",
        "PERIOD_UNIT": "hour"
    }
}
# m4.2xlarge 8CPU 32G
env_eks_model = {
    "environment": {
        "BUILD_NUMBER": "",
        "PROVISION_PLATFORM": "AWS-EKS",
        "NUMBER_OF_WORKERS": "3",
        "ENABLE_VORA_INSTALLATION": "false",
        "K8S_VERSION": "1.25",
        "EKS_AWS_REGION":"eu-west-1",
        "EKS_NODE_INSTANCE_TYPE":"m5.2xlarge",
        "PERIOD": "19",
        "PERIOD_UNIT": "hour",
        "ADD_INTO_FIREWALL_WHITELIST":"yes",
        "NETWORK_POLICY_ENFORCEMENT": "true",
        "EKS_PROJECT_ID": "DI-Dev(990498310577)"
    },
    "build_arguments": {
        "HELM_VERSION": "2.11.0"
    }
}
env_gardener_aws_model = {
    "environment": {
        "BUILD_NUMBER": "",
        "PROVISION_PLATFORM": "GARDENER-AWS",
        "NUMBER_OF_WORKERS": "3",
        "ENABLE_VORA_INSTALLATION": "false",
        "K8S_VERSION": "1.11.10",
        "AWS_REGION":"eu-central-1",
        "AWS_MACHINE_TYPE": "m4.xlarge",
        "AWS_VOLUME_SIZE": "50",
        "PERIOD": "16",
        "PERIOD_UNIT": "hour"
    }
}
env_dhaas_aws_model = {
    "environment": {
        "PERIOD": "21",
        "LANDSCAPE": "pushval",
        "REGIONAL_CLUSTER": "eu",
        "PROVISION_PLATFORM": "DHAAS-AWS",
        "PERIOD_UNIT": "hour",
        "ENABLE_VORA": "false",
        "K8S_VERSION": "1.19",
        "VORA_ADMIN_USERNAME": "system",
        "VORA_ADMIN_PASSWORD": random_password
    }
}
env_dhaas_azure_model = {
    "environment": {
        "PERIOD": "12",
        "LANDSCAPE": "testing",
        "REGIONAL_CLUSTER": "eu",
        "PROVISION_PLATFORM": "DHAAS-AZURE",
        "PERIOD_UNIT": "hour",
        "NUMBER_OF_WORKERS":"3",
        "DESCRIPTION":"dhaas-azure",
        "VORA_ADMIN_USERNAME": "system",
        "VORA_ADMIN_PASSWORD": random_password
    }
}
env_im_central_monitor_model = {
    'general': {'v2-registry-connection': True,
                'github-bdh-infra-tools': True
               },
    'GKE': {'latest_task_status_gke': False},
    'DHAAS-AWS': {'latest_task_status_dhaas': False,
                  'control-center': True}
    }

def init_logger(log_file_path):
    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create file handler and set level to debug
    fh = logging.FileHandler(log_file_path, mode='w')
    fh.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(lineno)d - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger

def update_env_when_upgrade():
    env_gke_model["environment"]["ENABLE_VORA_INSTALLATION"] = "true"
    env_gke_model["environment"]["SAP_DH_BIN_LEVEL"] = "milestone"
    env_gke_model["environment"]["VORA_VERSION"] = str(os.environ.get("BASE_BDH_VERSION"))
    env_gke_model["environment"]["EXPOSE_TEXT_ANALYSIS"] = "no"
    env_gke_model["environment"]["EXPOSE_VORA_TXC"] = "no"
    env_gke_model["environment"]["K8S_VERSION"] = "1.25"

    env_gke_model["environment"]["EXPOSE_VSYSTEM"] = "yes"
    env_gke_model["environment"]["BDH_INSTALL_OWN_REGISTRY"] = "yes"
    env_gke_model["environment"]["REGISTRY_AS_SHARED_CLUSTER"] = "no"
    if "BASE_VERSION_INSTALLATION_OPTIONS" in os.environ and os.environ["BASE_VERSION_INSTALLATION_OPTIONS"]:
        env_gke_model["environment"]["EXTRA_INSTALL_PARAMETERS"] = os.environ["BASE_VERSION_INSTALLATION_OPTIONS"]
    if env_gke_model["environment"]["VORA_VERSION"].startswith('2.7.'):
        env_gke_model["environment"]["K8S_VERSION"] = "1.15"
        env_gke_model["environment"]["INSTALL_VORA_VIA_SLCB"] = "false"
    env_gke_model["environment"]["VORA_PASSWORD"] = random_password
    env_gke_model["environment"]["VORA_SYSTEM_TENANT_PASSWORD"] = system_random_password

    env_eks_model["environment"]["ENABLE_VORA_INSTALLATION"] = "true"
    env_eks_model["environment"]["SAP_DH_BIN_LEVEL"] = "milestone"
    env_eks_model["environment"]["VORA_VERSION"] = str(os.environ.get("BASE_BDH_VERSION"))
    env_eks_model["environment"]["EXPOSE_TEXT_ANALYSIS"] = "no"
    env_eks_model["environment"]["EXPOSE_VORA_TXC"] = "no"
    env_eks_model["environment"]["K8S_VERSION"] = "1.24"
    env_eks_model["environment"]["EXPOSE_VSYSTEM"] = "yes"
    #env_eks_model["environment"]["BDH_INSTALL_OWN_REGISTRY"] = "yes" #With own registry, there was image mirroring failed issue
    env_eks_model["environment"]["REGISTRY_AS_SHARED_CLUSTER"] = "no"
    if "BASE_VERSION_INSTALLATION_OPTIONS" in os.environ and os.environ["BASE_VERSION_INSTALLATION_OPTIONS"]:
        env_eks_model["environment"]["EXTRA_INSTALL_PARAMETERS"] = os.environ["BASE_VERSION_INSTALLATION_OPTIONS"]
    if env_eks_model["environment"]["VORA_VERSION"].startswith('2.7.'):
        env_eks_model["environment"]["K8S_VERSION"] = "1.15"
        env_eks_model["environment"]["INSTALL_VORA_VIA_SLCB"] = "false"
    env_eks_model["environment"]["VORA_PASSWORD"] = random_password
    env_eks_model["environment"]["VORA_SYSTEM_TENANT_PASSWORD"] = system_random_password

    env_aks_model["environment"]["ENABLE_VORA_INSTALLATION"] = "true"
    env_aks_model["environment"]["SAP_DH_BIN_LEVEL"] = "milestone"
    env_aks_model["environment"]["VORA_VERSION"] = str(os.environ.get("BASE_BDH_VERSION"))
    env_aks_model["environment"]["EXPOSE_TEXT_ANALYSIS"] = "no"
    env_aks_model["environment"]["EXPOSE_VORA_TXC"] = "no"
    env_aks_model["environment"]["K8S_VERSION"] = "1.24"
    env_aks_model["environment"]["EXPOSE_VSYSTEM"] = "yes"
    env_aks_model["environment"]["BDH_INSTALL_OWN_REGISTRY"] = "yes"
    env_aks_model["environment"]["REGISTRY_AS_SHARED_CLUSTER"] = "no"
    if "BASE_VERSION_INSTALLATION_OPTIONS" in os.environ and os.environ["BASE_VERSION_INSTALLATION_OPTIONS"]:
        env_aks_model["environment"]["EXTRA_INSTALL_PARAMETERS"] = os.environ["BASE_VERSION_INSTALLATION_OPTIONS"]
    env_aks_model["environment"]["VORA_PASSWORD"] = random_password
    env_aks_model["environment"]["VORA_SYSTEM_TENANT_PASSWORD"] = system_random_password

    env_dhaas_aws_model["environment"]["ENABLE_VORA_INSTALLATION"] = "true"
    env_dhaas_aws_model["environment"]["VORA_VERSION"] = str(os.environ.get("BASE_BDH_VERSION"))

    if "BASE_VERSION_INSTALLATION_OPTIONS" in os.environ and os.environ["BASE_VERSION_INSTALLATION_OPTIONS"]:
        env_dhaas_aws_model["environment"]["EXTRA_INSTALL_PARAMETERS"] = os.environ["BASE_VERSION_INSTALLATION_OPTIONS"]

    env_dhaas_azure_model["environment"]["ENABLE_VORA_INSTALLATION"] = "true"
    env_dhaas_azure_model["environment"]["VORA_VERSION"] = str(os.environ.get("BASE_BDH_VERSION"))

    if "BASE_VERSION_INSTALLATION_OPTIONS" in os.environ and os.environ["BASE_VERSION_INSTALLATION_OPTIONS"]:
        env_dhaas_azure_model["environment"]["EXTRA_INSTALL_PARAMETERS"] = os.environ["BASE_VERSION_INSTALLATION_OPTIONS"]

    #Currently for DI 3.2 we didn't support k8s 1.26+, so we will use the 1.24 upgrade to 1.25 instead. 
    #This code is only working in milestone_validation_upgrade job. 
    target_vora_version = str(os.environ.get("VORA_VERSION"))
    if target_vora_version.startswith('3.2.'):
        if env_eks_model["environment"]["VORA_VERSION"].startswith('3.2.'):
            env_eks_model["environment"]["K8S_VERSION"] = "1.24"
        if env_gke_model["environment"]["VORA_VERSION"].startswith('3.2.'):
            env_gke_model["environment"]["K8S_VERSION"] = "1.24"
        if env_aks_model["environment"]["VORA_VERSION"].startswith('3.2.'):
            env_aks_model["environment"]["K8S_VERSION"] = "1.24"

def update_env_for_auto_env():
    env_gke_model["environment"]["GCP_IMAGE_TYPE"] = os.environ.get("GCP_IMAGE_TYPE", "cos")
    env_gke_model["environment"]["K8S_VERSION"] = os.environ.get("K8S_VERSION", "1.19")

    env_gke_model["environment"]["NETWORK_POLICY_ENFORCEMENT"] = os.environ.get("NETWORK_POLICY_ENFORCEMENT", "true")
    env_gke_model["environment"]["PERIOD"] = "24"

    env_aks_model["environment"]["K8S_VERSION"] = os.environ.get("K8S_VERSION", "1.20")
    env_aks_model["environment"]["NETWORK_POLICY_ENFORCEMENT"] = os.environ.get("NETWORK_POLICY_ENFORCEMENT", "true")
    env_aks_model["environment"]["PERIOD"] = "24"

    env_eks_model["environment"]["K8S_VERSION"] = os.environ.get("K8S_VERSION", "1.19")
    env_eks_model["environment"]["NETWORK_POLICY_ENFORCEMENT"] = os.environ.get("NETWORK_POLICY_ENFORCEMENT", "true")
    env_eks_model["environment"]["PERIOD"] = "24"

def get_azure_registry_name():
    azure_registry_name = "infrabase"
    # if AKS_SUBSCRIPTION_NAME is set, means on new AKS subscription, infrabase can't be found
    if provision_platform.upper() == "AZURE-AKS" and "AKS_SUBSCRIPTION_NAME" in os.environ and os.environ.get('AKS_SUBSCRIPTION_NAME') == "sap-pi-big-data-validation":
        # on new azure installation: create dedicated registry for vflow;
        # use shared registry for installation
        # workaround for: DM01-1708 Installation failed on DI 3.0.96 AKS
        #azure_registry_name = "dhvalregistry"
        #azure_registry_name = "azureaksrepo" + str(int(time.time() * 1000))
        azure_registry_name = "di-dev-cicd-registry.common.repositories.cloud.sap"
    return  azure_registry_name

def check_datahub_installed():
    if upgrade_test.lower() == "yes" or provision_platform.lower().startswith("dhaas-"):
        return True
    return False

def isBdhVersionSupportSingleNode():
    bdhVersion = str(os.getenv("BASE_BDH_VERSION"))
    version = re.split("[-]", bdhVersion)
    version = version[0].split(".")

    if int(version[0]) < 2:
        return False
    if int(version[0]) == 2 and int(version[1]) < 5:
        return False
    return True

def runRequest(function, *args, **kwargs):
    """
    call restAPI for max $max_error_num times trials
    """
    error_num = 0
    print_ret_content = True
    if kwargs.get('print_ret_content') is not None:
        print_ret_content = kwargs.get('print_ret_content')
        del kwargs['print_ret_content']
    while True:
        try:
            ret = function(*args, verify=False, **kwargs)
        except Exception as e:
            logger.warning( "Request got exception for %s " % str(e))
            error_num = error_num + 1
            # retry for max_error_retry_num
            if error_num < max_error_retry_num:
                logger.info( "Wait for %d seconds and retry" % check_interval)
                time.sleep(check_interval)
            else:
                logger.error( "Fail to make request for getting exceptions for %d seconds!" % max_error_retry_num)
                raise
        else:
            if print_ret_content:
                logger.debug( "Make request to server, return message is:\n status_code:%d,\n content:%s" % (ret.status_code, ret.content) )
            return ret

def checkQuota(header):
    """
    Check the quota from GKE
    - if return status is 200 and the quota number is less than or equal to gke_zone_quota_threshold, return 0
    - if return status is 200 and the quota number is large than gke_zone_quota_threshold, return 1
    - if return status is not 200, return 2

    return the status code
    """
    ret_val = 0
    item = {}
    if provision_platform.upper() != "GKE":
        return ret_val
    for item in env_optional_gke_zone:
        url = '%s/api/v1/clusters/count/GKE/%s' % (base_url, item["GCP_ZONE"])
        ret = runRequest(requests.get, url, headers=header)
        if ret.status_code == 200:
            data = ret.json()
            consumed = data['count']
            if consumed < gke_zone_quota_threshold: #pylint: disable=no-else-break
                logger.info("Use zone %s, which consumed %d nodes" % (item["GCP_ZONE"], consumed))
                ret_val = 0
                break
            else:
                logger.error("Zone %s, has consumed %d nodes, more than %d, try the next zone." % (item["GCP_ZONE"], consumed, gke_zone_quota_threshold))
                ret_val = 1
        else:
            ret_val = 2
            logger.error("check quota api return status code %d" % ret.status_code)

    if ret_val != 0:
        logger.error( "All zones are out of juice, no available room for new cluster! Or rest api error %d" % ret.status_code)
        return ret_val

    env_gke_model["environment"]["GCP_ZONE"] = item["GCP_ZONE"]
    env_gke_model["environment"]["GCLOUD_K8S_SUBNETWORK"] = item ["GCLOUD_K8S_SUBNETWORK"]
    return ret_val

def applyForEnv(owner, header, tag, use_for, azure_registry_name):
    """
    Apply for kubernetes environment.
    - if return status is 200, return
    - if return status is 403 (predefined for exceed max resource request threshold), wait and loop request for 2 hour
    - if return status is other unexpected code, try max 3 times

    :return: cluster_name
    """
    INSTALLER_VALIDATION = os.environ.get("INSTALLER_VALIDATION", "no")
    if provision_platform.upper() == "MONSOON":
        env = env_on_premise_model
    elif provision_platform.upper() == "GKE" or provision_platform.upper() == "GCP-GKE":
        if "GCP_PROJECT_ID" in os.environ and os.environ["GCP_PROJECT_ID"] is not None:
            env_gke_model["environment"]["GCP_PROJECT_ID"] = os.environ["GCP_PROJECT_ID"] 
        if "GKE_K8S_VPC" in os.environ and os.environ["GKE_K8S_VPC"] is not None:
            env_gke_model["environment"]["GKE_K8S_VPC"] = os.environ["GKE_K8S_VPC"]
        if "GKE_LATEST_K8S_VERSION" in os.environ and os.environ["GKE_LATEST_K8S_VERSION"]:
            env_gke_model["environment"]["K8S_VERSION"] = os.environ["GKE_LATEST_K8S_VERSION"]
        env = env_gke_model
    elif provision_platform.upper() == "AZURE-AKS":
        env = env_aks_model
        # To Fix the BDH-13637 remove the if/else for upgrade_test 
        env["environment"]["AZURE_REGISTRY_NAME"] = azure_registry_name
        if 'AKS_SUBSCRIPTION_NAME' in os.environ:
            env["environment"]["AKS_SUBSCRIPTION_NAME"] = os.environ['AKS_SUBSCRIPTION_NAME']
        setAKSRegistryToBASEVERSION()
    elif provision_platform.upper() == "AWS-EKS":
        env = env_eks_model
    elif provision_platform.upper() == "GARDENER-AWS":
        env = env_gardener_aws_model
    elif provision_platform.upper() == "GARDENER-CCLOUD":
        env = env_gardener_ccloud_model    
    elif provision_platform.upper() == "DHAAS-AWS" or provision_platform.upper() == "DHAAS-AZURE":
        env = env_dhaas_aws_model if provision_platform.upper() == "DHAAS-AWS" else env_dhaas_azure_model
        if "K8S_VERSION" in os.environ and os.environ["K8S_VERSION"]:
            env["environment"]["K8S_VERSION"] = os.environ["K8S_VERSION"]
        if upgrade_test.lower() != "yes":
            if 'VORA_VERSION' in os.environ:
                env["environment"]['VORA_VERSION'] = os.environ['VORA_VERSION']
                # save the VORA_VERSION for the import_export_test use. because it need to pull the image in DI validation
                with open(bdh_base_version_file, 'a+') as f:
                    f.write("export VORA_VERSION=%s\n" % str(os.environ['VORA_VERSION']))
            elif 'BUILD_VERSION' in os.environ:
                env["environment"]['VORA_VERSION'] = os.environ['BUILD_VERSION']

        with open(bdh_base_version_file, 'a+') as f:
            f.write("export VORA_PASSWORD='%s'\n" % random_password)
            f.write("export VORA_TENANT=default\n")    
        if any([env["environment"]['VORA_VERSION'].startswith(prefix) for prefix in ['2107','2103','2108']]) or os.environ.get("GERRIT_CHANGE_BRANCH", "") in ['rel-2103', 'rel-2107', 'rel-2108']:
            env["environment"]['ENABLE_VORA'] = 'true'
    else:
        raise RuntimeError("Unsupported provision_platform:%s" % provision_platform)

    #Add VORA_VERSION for IM task
    if ('VORA_VERSION' in os.environ) and ('VORA_VERSION' not in env["environment"]):
        env["environment"]['VORA_VERSION'] = os.environ['VORA_VERSION']

    if upgrade_test.lower() == "yes":
        base_version = str(os.environ.get("BASE_BDH_VERSION"))
        if any([base_version.startswith(prefix) for prefix in ['3.']]):
            env["environment"]["INSTALL_VORA_VIA_SLCB"] = "true"
    env["environment"]["OWNER"] = owner
    env["environment"]["TAG"] = tag
    env["environment"]["DESCRIPTION"] = '%s %s %s' % (tag, provision_platform, os.environ.get('INFRABOX_BUILD_URL'))
    if "GERRIT_CHANGE_URL" in os.environ:
        env["environment"]["DESCRIPTION"] = '%s %s' % (env["environment"]["DESCRIPTION"], os.environ['GERRIT_CHANGE_URL'])

    # In hanalite-releasepack push validation whitelist doesn't need to be configured, but it's needed in component push validation
    # like datahub-app-base.
    # FORCE_ADD_INTO_FIREWALL_WHITELIST is configured in ODTEM database hanalite-lib common template.
    if 'PERIOD' in os.environ:
        env["environment"]["PERIOD"] = os.environ["PERIOD"]
    if use_for == 'PUSH_VALIDATION' and 'ADD_INTO_FIREWALL_WHITELIST' in env['environment']:
        if 'FORCE_ADD_INTO_FIREWALL_WHITELIST' in os.environ and os.environ['FORCE_ADD_INTO_FIREWALL_WHITELIST'] == 'yes':
            pass
        else:
            env['environment'].pop('ADD_INTO_FIREWALL_WHITELIST')

    if provision_platform.upper() == "MONSOON":
        if  str(os.environ.get("OFFLINE_INSTALL", "no")) == "yes":
            env["environment"]["MONSOON_VOLUME_SIZE"] = "320"
        if 'MONSOON_AWS_ACCESS_KEY' not in os.environ or 'MONSOON_AWS_SECRET_KEY' not in os.environ: #pylint: disable=no-else-raise
            raise RuntimeError("Missing MONSOON_AWS_ACCESS_KEY or MONSOON_AWS_SECRET_KEY configuration!")
        else:
            env["environment"]["AWS_ACCESS_KEY"] = os.environ['MONSOON_AWS_ACCESS_KEY']
            env["environment"]["AWS_SECRET_KEY"] = os.environ['MONSOON_AWS_SECRET_KEY']
    logger.debug(env)
    url = '%s/api/v1/tasks/deployment' % (base_url)

    fail_num = 0
    start_time = time.time()
    max_refuse_time = int(os.environ.get("MAX_REFUSE_WAIT", 7200))
    while True:
        ret = runRequest(requests.post, url, json=env, headers=header)
        status = ret.status_code
        if status == 200:
            data = ret.json()
            logger.info(data)
            cluster_name = data['cluster_name']
            url = data['url']
            logger.info("## Successfully make request for kubernetes cluster, cluster name is %s, build url is %s" % (cluster_name, url))
            bucket_name = None
            if 'bucket_name' in data:
                bucket_name = data['bucket_name']
                logger.info("Extra bucket created: %s" % bucket_name)
            shoot_name = None
            if 'shoot_name' in data:
                shoot_name = data['shoot_name']
                logger.info("Extra shoot name generated: %s" % shoot_name)

            return cluster_name, url, bucket_name, shoot_name, env
        elif status == 403:
            # when got refused by reached max request threshold, wait and retry
            if time.time() - start_time < max_refuse_time:
                logger.warning( "Got refused by server for reaching resource threshold, wait for %d seconds and retry" % check_interval)
                time.sleep(check_interval)
            else:
                raise RuntimeError("Got refused for kubernetes cluster creation after %d seconds!" % (max_refuse_time) )
        else:
            # other errors from server
            logger.warning( "Got unexpected status_code from server, status_code is %d, error information is %s " % (ret.status_code, ret.content))
            fail_num = fail_num + 1
            if fail_num < max_error_retry_num:
                logger.info( "Wait for %d seconds and retry" % check_interval)
                time.sleep(check_interval)
            else:
                raise RuntimeError("Fail to request kubernetes cluster for for %d times!" % max_error_retry_num)

def deleteCluster(cluster_name, header):
    """
    delete cluster, and don't care about the result
    """
    url = '%s/api/v1/tasks/%s' % (base_url, cluster_name)
    runRequest(requests.delete, url, headers=header)

def hibernateWakeupCluster(owner, cluster_name, header, pods_number=0):
    """
    hibernate/wakeup cluster
    Params:
      pods_number = 0  -- hibernate cluster
      pods_number > 0  -- wakeup cluster (for CI, default set to 3)
      pods_number < 0  -- illegial value
    """
    max_refuse_time = int(os.environ.get("MAX_REFUSE_WAIT", 7200))

    if pods_number > 0:
        expectStatus = 'running'
    else:
        pods_number = 0
        expectStatus = 'hibernated'
    url = '%s/api/v1/clusters/%s/%s' % (base_url, cluster_name, str(pods_number))
    fail_num = 0
    while fail_num < max_error_retry_num:
        ret = runRequest(requests.patch, url, headers=header)
        if ret.status_code != 200:
            logger.warning("Call RestAPI to hibernate/wakeup cluster %s failed - %d.\n RestAPI call url: %s" % (cluster_name, fail_num, url))
            time.sleep(check_interval)
            fail_num += 1
        else:
            break
    if fail_num == max_error_retry_num:
        return False
    start_time = time.time()
    while True:
        fail_num = 0
        while fail_num < max_error_retry_num:
            clsStatus = getClusterStatus(owner, cluster_name, header)
            if clsStatus is None:
                logger.warning("Get status for cluster %s failed - %d" % (cluster_name, fail_num))
                time.sleep(check_interval)
                fail_num += 1
            else:
                break
        if fail_num == max_error_retry_num:
            return False
        if clsStatus == expectStatus:
            return True
        else:
            if time.time() - start_time < max_refuse_time:
                logger.warning("Current status of cluster %s is %s ..." % (cluster_name, clsStatus))
                time.sleep(check_interval)
            else:
                logger.warning("Get expected status '%s' for cluster %s failed after %s seconds." % (expectStatus, cluster_name, max_refuse_time))
                return False

def getClusterStatus(owner, cluster_name, header):
    """
    get Cluster Status
    """
    #
    # The IM RestAPI to get cluster stats will return a JSON format data as
    #   {
    #       "status": "200",
    #       "tasks": "[ ... ...]"
    #   }
    # Here we parse the "tasks" to get cluster status value.
    #
    # function getClusterStatusLog will get the value from "tasks"
    #
    clusterStatus = None
    output = getClusterStatusLog(cluster_name, header, owner)
    if output is None:
        logger.warning("Get status for cluster %s failed" % cluster_name)
        return clusterStatus
    try:
        output = output.strip().replace('\\n','').replace('\\','')
        dataList = json.loads(output)
        #
        #  dataList[0][0] -- cluster name
        #  dataList[0][1] -- cluster owner
        #  dataList[0][2] -- cluster platform (GCP-GKE/AKS/EKS/etc.)
        #  dataList[0][6] -- cluster environment
        #  ... ...
        #  dataList[0][17] -- cluster status
        #
        clusterStatus = dataList[0][17]
    except Exception as e:
        logger.error("Got error '%s' when call getClusterStatus()" % str(e))
    finally:
        return clusterStatus # pylint:disable=lost-exception

def getClusterStatusLog(cluster_name, header, owner):
    # get the Cluster info
    url = base_url + '/api/v1/tasks/deployment/' + owner + '?kc_name=' + cluster_name
    ret = runRequest(requests.get, url, headers=header)
    if ret.status_code == 200:
        data = ret.json()
        if 'tasks' in data and len(data['tasks']) != 0:
            return data['tasks']
    logger.warning("Get log for cluster %s failed" % cluster_name)
    return None

def getPodLogForDHAAS(cluster_name,header):
    """
    get the dhaas pod log. For DHAAS-AWS only
    """
    dhaas_pod_log_file = '/infrabox/upload/archive/dhaas_pod_log_'

    if provision_platform.upper() != "DHAAS-AWS":
        logger.warning( "Only can get pod log from DHAAS-AWS" )
        return
    url = '%s/api/v1/clusters/logs/pods/%s' % (base_url, cluster_name)
    proxies = {"http": None,"https": None,}
    ret = runRequest(requests.get, url, proxies=proxies, headers=header, print_ret_content=False)
    if ret.status_code == 200:
        if ret.content is not None:
            with open(dhaas_pod_log_file + time.strftime('%Y_%m_%d_%H_%M_%S') + '.zip', "wb") as pod_log_file:
                pod_log_file.write(ret.content)
            logger.info("Save DHAAS pod log to: %s. Cluster:  %s" %(dhaas_pod_log_file,cluster_name))
        else:
            logger.warning("Get empty DHAAS pod log, discard it. Cluster: %s" %cluster_name)
    else:
        logger.error("Error when request for DHAAS pod log. Error code: %d, error message: %s" %(ret.status_code,str(ret.content)))

def printLogtoFile(output, file_path):
    logger.info("Installer Log: %s " % json.dumps(output, sort_keys=True, indent=4))
    with open(file_path, 'w') as outfile:
        json.dump(output, outfile)

def getClusterDeploymentLog(cluster_name, header, owner):
    # get the DI logs when the installer even not start
    url = base_url + '/api/v1/tasks/deployment/' + owner + '?page=1&per_page=10&kc_name=' + cluster_name
    ret = runRequest(requests.get, url, headers=header)
    if ret.status_code == 200:
        data = ret.json()
        if 'tasks' in data and len(data['tasks']) != 0:
            return data['tasks']

    logger.warning("Get installer log for %s failed" % cluster_name)
    return None

def getAKSClusterResourceInfo(cluster_name, header):
    url = base_url + '/api/v1/clusters/k8s?page=1&per_page=10&kc_name=' + cluster_name
    ret = runRequest(requests.get, url, headers=header)
    if ret.status_code == 200:
        data = ret.json()
        clusters = data['clusters']
        if len(clusters) == 0:
            logger.warning("Get resource group for cluster %s failed" % cluster_name)
            return None
        else:
            clusters = json.loads(clusters)
            if len(clusters) == 0:
                logger.warning("Get resource group for cluster %s failed" % cluster_name)
                return None
            return clusters[0]['kc_dply_cfg']['environment']['AZURE_REGISTRY_NAME'],\
            clusters[0]['kc_dply_cfg']['environment']['AZURE_RESOURCE_GROUP']

    logger.warning("Get resource group for cluster %s failed" % cluster_name)
    return None

def getClusterInstallLogForDHAAS(cluster_name, header, owner):
    """
    get the installer log. For DHAAS-AWS only
    """
    if provision_platform.upper() != "DHAAS-AWS":
        logger.warning( "Only DHAAS-AWS installer log be supported" )
        return False

    url = '%s/api/v1/clusters/logs/%s' % (base_url, cluster_name)
    ret = runRequest(requests.get, url, headers=header)
    if ret.status_code != 200:
        logger.warning("Get installer log for %s failed" % cluster_name)
        return False

    data = ret.json()

    if 'log_data' in data and data['log_data']:
        output = data['log_data']
    else:
        output = getClusterDeploymentLog(cluster_name, header, owner)

    if output is None:
        logger.warning("Get empty installer log for %s failed" % cluster_name)
        return False

    printLogtoFile(output, '/infrabox/upload/archive/dhaas_creation_fail_log.json')
    return True

def checkDataHubInstallationReady(cluster_name, header, owner, env):
    """
    check datahub installation is ready
    if ready return True
    else return false
    """
    url = '%s/api/v1/clusters/bdh/%s?page=1&&per_page=10&bdh_name=%s' % (base_url, owner, cluster_name)
    clusters = None
    for i in range(5):
        logger.info("Check if DataHub installation is ready for %d time" % (i+1))
        ret = runRequest(requests.get, url, headers=header)
        if ret.status_code == 200:
            data = ret.json()
            clusters = data['clusters']
            if len(clusters) != 0 and len(json.loads(clusters)) != 0 :
                break
            else:
                time.sleep(180)
                continue
        else:
            time.sleep(180)
            continue
    if clusters != None and len(clusters) != 0:
        clusters = json.loads(clusters)
        if len(clusters) == 0:
            return False
        is_vsystem_parsed = False
        for item in clusters[0]['bdh_info']:
            if item['name'] == 'datahub system tenant password':
                with open(bdh_base_version_file, 'a+') as f:
                    f.write("export VORA_SYSTEM_TENANT_PASSWORD='%s'\n" % str(item['value']))
            if item['name'] == 'datahub user tenant password':
                with open(bdh_base_version_file, 'a+') as f:
                    f.write("export VORA_PASSWORD='%s'\n" % str(item['value']))
            if item['name'] == 'datahub launch-pad endpoint':
                with open(bdh_base_version_file, 'a+') as f:
                    f.write("export VSYSTEM_ENDPOINT=%s\n" % str(item['value']))
                is_vsystem_parsed = True
            if item['name'] == 'gcloud storage bucket name':
                with open(bdh_base_version_file, 'a+') as f:
                    f.write("export K8S_CLUSTER_NAME=%s\n" % str(item['value']))
            if item['name'] == 'kubernetes version':
                env["environment"]["K8S_VERSION"] = str(item['value'])
            if item['name'] == 'datahub user tenant name':
                with open(bdh_base_version_file, 'a+') as f:
                    f.write("export VORA_TENANT=%s\n" % str(item['value']).lower())
            if item['name'] == 'datahub system tenant name':
                with open(bdh_base_version_file, 'a+') as f:
                    f.write("export VORA_SYSTEM_TENANT=%s\n" % str(item['value']).lower())
            if item['name'] == 'datahub user/system tenant user' or item['name'] == 'datahub system tenant user':
                with open(bdh_base_version_file, 'a+') as f:
                    f.write("export VORA_USERNAME=%s\n" % str(item['value']).lower())
            if item['name'] == 'azure container registry password':
                with open(bdh_base_version_file, 'a+') as f:
                    f.write("export AZURE_DOCKER_LOGIN_PASSWORD='%s'\n" % str(item['value']))
            if item['name'] == 'azure container registry username':
                with open(bdh_base_version_file, 'a+') as f:
                    f.write("export AZURE_DOCKER_LOGIN_USERNAME='%s'\n" % str(item['value']))
            if item['name'] == 'azure container registry address':
                with open(bdh_base_version_file, 'a+') as f:
                    f.write("export AZURE_DOCKER_LOGIN_ADDRESS='%s'\n" % str(item['value']))
        if 'VORA_ADMIN_PASSWORD' in clusters[0]['kc_dply_cfg']['environment']:
            with open(bdh_base_version_file, 'a+') as f:
                f.write("export VORA_PASSWORD='%s'\n" % str(clusters[0]['kc_dply_cfg']['environment']['VORA_ADMIN_PASSWORD']))
                f.write("export VORA_TENANT=%s\n" % 'default')
        if not is_vsystem_parsed and 'bdh_vsys_url' in clusters[0]:
            with open(bdh_base_version_file, 'a+') as f:
                f.write("export VSYSTEM_ENDPOINT=%s\n" % str(clusters[0]['bdh_vsys_url']))
        return True
    else:
        return False

def setAKSRegistryToBASEVERSION():
    url = '%s/api/v1/configs/crdls/milestone_validation' % (base_url)
    ret = runRequest(requests.get, url, headers=header)
    if ret.status_code == 200:
        data = ret.json()
        clusters = data['credentials']
        azure_docker_login_address = clusters['AZURE-AKS']["registry_full_access"]['azure container registry address']
        azure_docker_login_username = clusters['AZURE-AKS']["registry_full_access"]['azure container registry username']
        azure_docker_login_password = clusters['AZURE-AKS']["registry_full_access"]['azure container registry password']
        with open(azure_cert_file, 'a+') as f:
            f.write("export AZURE_DOCKER_LOGIN_PASSWORD='%s'\n" % azure_docker_login_password)
        with open(azure_cert_file, 'a+') as f:
            f.write("export AZURE_DOCKER_LOGIN_USERNAME='%s'\n" % azure_docker_login_username)
        with open(azure_cert_file, 'a+') as f:
            f.write("export AZURE_DOCKER_LOGIN_ADDRESS='%s'\n" % azure_docker_login_address)


def checkEnvReady(cluster_name, header, owner, env):
    """
    check the cluster is ready
    - if not ready, wait and loop for 1 hour
    - if failed, directly raise exception

    :param cluster_name: the kubernetes cluster name
    :return: True for ready; raise Exception for not ready in predefined time

    ** set of legal value returned from infrastructure ['ready', 'reserved', 'failed', 'error', 'removed', 'deploying', 'undeploying', 'timeout']
    """
    # check for environment is Ready
    use_for = env["environment"]["TAG"]
    max_wait_ready_time = int(os.environ.get("MAX_READY_WAIT", 3600))
    get_pod_log_cycle = 10 * 60
    url = '%s/api/v1/clusters/k8s/status/%s' % (base_url, cluster_name)
    start_time = time.time()
    get_pod_log_time_threshold = get_pod_log_cycle # pylint: disable=unused-variable
    admin_conf_file = os.path.join('/tmp', 'admin.conf')
    while time.time() - start_time < max_wait_ready_time:
        ret = runRequest(requests.get, url, headers=header)
        if ret.status_code == 200:
            data = ret.json()
            cluster_status = data['cluster_status']
            if cluster_status.upper() == 'READY':
                if check_datahub_installed():
                    # check datahub is installed
                    if not checkDataHubInstallationReady(cluster_name, header, owner, env):
                        getClusterInstallLogForDHAAS(cluster_name, header, owner)
                        getPodLogForDHAAS(cluster_name,header)
                        if use_for.upper() == 'MILESTONE_VALIDATION' and provision_platform.upper() == 'DHAAS-AWS':
                            logger.warning("Cluster is reserved for 16 hours")
                        else:
                            deleteCluster(cluster_name, header)
                            logger.info("Cluster is deleted")
                        if job_action.upper() == 'CREATE':
                            message = "Kubernetes cluster %s creation ready, but DataHub installation failed!" % cluster_status.upper()
                        if provision_platform.upper() == 'DHAAS-AWS':
                            message = 'DI Instance %s READY, but IM parse the DH logon credential failed! Please check the cluster: %s info on IM.' % (job_action, cluster_name)
                        raise RuntimeError(message)
                dump_logs('successful')
                logger.info("Kubernetes cluster is READY!")
                return True
            elif cluster_status.upper() in ['FAILED', 'ERROR', 'REMOVED', 'UNDEPLOYING', 'TIMEOUT']:
                if provision_platform.upper() == 'DHAAS-AWS':
                    getClusterInstallLogForDHAAS(cluster_name, header, owner)
                    getPodLogForDHAAS(cluster_name,header)
                    dump_logs('unsuccessful')
                if use_for.upper() == 'MILESTONE_VALIDATION' and provision_platform.upper() == 'DHAAS-AWS':
                    logger.warning("Cluster is reserved for 16 hours")
                else:
                    deleteCluster(cluster_name, header)
                    logger.info("Cluster is deleted")
                raise RuntimeError("Kubernetes cluster %s status is %s ! Stop waiting when met this type of status!" % (job_action, cluster_status.upper()))
            elif cluster_status.upper() == 'DEPLOYING' and time.time() - start_time > get_pod_log_time_threshold:
                #get pod log every 10 mins
                if provision_platform.upper() == 'DHAAS-AWS':
                    logger.warning("pods log threshold time is: %d" % get_pod_log_time_threshold)
                    get_pod_log_time_threshold += get_pod_log_cycle
                    logger.warning("The absolute time of the present: %d" % (time.time() - start_time))
                    logger.warning("Get Kubernetes cluster pods log cyclically")
                    if os.path.exists(admin_conf_file):
                        dhaas_pod_log_file = '/infrabox/upload/archive/dhaas_pod_log_' + time.strftime('%Y_%m_%d_%H_%M_%S') + '.log'
                        cmd='export KUBECONFIG=' + admin_conf_file + '&& kubectl logs datahub-operator-0 -n datahub-system \
                            > ' + dhaas_pod_log_file
                        os.system(cmd)
                    else:
                        url_kubecfg = '%s/api/v1/clusters/dhaas/%s' % (base_url, cluster_name)
                        ret = runRequest(requests.get, url_kubecfg, headers=header)
                        if ret.status_code == 200:
                            data = ret.json()
                            if 'kubecfg' in data and data['kubecfg'] is not None and data['kubecfg'] != '':
                                write_conf_file(cluster_name, header, admin_conf_file, data)
                                dhaas_pod_log_file = '/infrabox/upload/archive/dhaas_pod_log_' + time.strftime('%Y_%m_%d_%H_%M_%S') + '.log'
                                cmd='export KUBECONFIG=' + admin_conf_file + '&& kubectl logs datahub-operator-0 -n datahub-system \
                                    > ' + dhaas_pod_log_file
                                os.system(cmd)
                            else:
                                logger.warning("Fail to get admin.conf file because kubecfg is null")
                        else:
                            logger.warning("Fail to get admin.conf file from IM api:%s when cluster_status is deploying" % url_kubecfg)
            else:
                logger.warning("Kubernetes cluster %s status is: %s " % (job_action, cluster_status.upper()))
        else:
            logger.warning("Got unexpected status_code from server, status_code is %d, error information is %s" % (ret.status_code, ret.content))

        logger.warning("Check kubernets cluster is NOT Ready yet, wait another %d seconds!" % check_interval)
        time.sleep(check_interval)

    raise RuntimeError("Kubernetes cluster is NOT Ready after %d seconds!" % (max_wait_ready_time))

def dump_logs(status):
    try:
        logger.info('[%s] collecting di setup logs' % (status))
        os.system('/project/debug_di_setup.sh')
    except Exception as e:
        logger.error(e)
        logger.error('Error occurred while dumping logs')

def get_dhop_backup_name(cluster_name):
    url = base_url + "/api/v1/clusters/dhop_backup_name/" + cluster_name

    wait = 0
    wait_time = 900
    while wait < wait_time:
        ret = runRequest(requests.get, url, headers=header)
        if ret.status_code == 200:
            if ret.content.decode() != '[]':
                return eval(ret.content.decode())[0]
        else:
            logger.warning("Call RestAPI to get cluster %s dhop_backup_name failed.\n RestAPI call url: %s" % (cluster_name, url))
        time.sleep(check_interval)
        wait += 30
        if wait >= wait_time:
            logger.warning("Call RestAPI to get cluster %s dhop_backup_name failed even wait %d." % (cluster_name, wait_time))
            return ''

def getEnv(cluster_name):
    env = {
        "environment": {}
    }
    env["environment"]["VERSION"] = str(os.environ.get("VORA_VERSION", ""))
    if len(env["environment"]["VERSION"]) == 0:
        logger.error("No VORA_VERSION been set!")
        raise RuntimeError("Failed to restore cluster %s" %cluster_name)
    env["environment"]["TAG"] = str(os.environ.get("USE_FOR", "MILESTONE_VALIDATION"))
    if job_action.upper() == 'RESTORE':
        backup_name_file="/infrabox/inputs/dhaas_backup_" + "_".join(provision_platform.lower().split('-')) + "/backup_name.txt"
        if os.path.exists(backup_name_file):
            with open(backup_name_file, "r") as f:
                env["environment"]["BACKUP_NAME"] = f.read().strip('\n')
        else:
            logger.error("No backup name was found. DI cluster restore will fail!")
            raise RuntimeError("Failed to restore cluster %s" %cluster_name)

        if int(env["environment"]["VERSION"].split('.')[0]) > 2109:
            dhop_backup_name = get_dhop_backup_name(cluster_name)
            if dhop_backup_name != '':
                env["environment"]["DHOP_BACKUP_NAME"] = dhop_backup_name
            else:
                raise RuntimeError("failed to get dhop_backup_name for restore")
   
    return env

def startDIClusterRestore(cluster_name, header, env):
    url = base_url + "/api/v1/tasks/restore/" + cluster_name
    ret = runRequest(requests.post, url, json=env, headers=header)
    if ret.status_code == 200:
        data = ret.json()
        cluster_name = data['output']
        return cluster_name
    else:
        raise RuntimeError("Fail to restore DI cluster")

def restoreDIClusterByIM(owner,header,cluster_name):
    env = getEnv(cluster_name)
    logger.debug("Restore env is %s." % (env))
    newCluster = startDIClusterRestore(cluster_name, header, env)
    if not checkEnvReady(newCluster, header, owner, env):
        logger.error("DI cluster restore fail!")
        return False, None, env
    return True, newCluster, env

def waitStatusReady(owner, cluster_name, header, env, BACKUP_NAME=None):
    # check for environment is Ready
    max_wait_ready_time = int(os.environ.get("MAX_READY_WAIT", 5400))
    waitStatus=[]
    url = '%s/api/v1/clusters/k8s/monitor/status/%s' % (base_url, cluster_name)
    if job_action.upper() == 'UPGRADE':
        waitStatus=['UPGRADING', 'UPDATING DATAHUB']
    elif job_action.upper() == 'BACKUP':
        if BACKUP_NAME is None or BACKUP_NAME == '':
            raise RuntimeError("No backup name, failed to backup DI cluster")
        waitStatus=['BACKUPING', 'PENDING', 'BACKUP RUNNING']
        url = '%s/api/v1/clusters/k8s/backup/status/%s/%s' % (base_url, cluster_name, BACKUP_NAME)
    start_time = time.time()
    while time.time() - start_time < max_wait_ready_time:
        ret = runRequest(requests.get, url, headers=header)
        if ret.status_code == 200:
            data = ret.json()
            cluster_status = ''
            if job_action.upper() == 'BACKUP':
                cluster_status = data['backup_status']
            else:
                cluster_status = data['monitor_status']
            if cluster_status.upper() in ['READY']:
                if job_action.upper() == 'UPGRADE':
                    if not checkDataHubInstallationReady(cluster_name, header, owner, env):
                        getClusterInstallLogForDHAAS(cluster_name, header, owner)
                        getPodLogForDHAAS(cluster_name,header)
                        if use_for.upper() == 'MILESTONE_VALIDATION' and provision_platform.upper() == 'DHAAS-AWS':
                            logger.warning("Cluster is reserved for 16 hours")
                        else:
                            deleteCluster(cluster_name, header)
                            logger.info("Cluster is deleted")
                        if provision_platform.upper() == 'DHAAS-AWS':
                            message = 'DI Instance %s READY, but IM parse the DH logon credential failed! Please check the cluster: %s info on IM.' % (job_action, cluster_name)
                        raise RuntimeError(message)
                logger.info("DI cluster %s is Ready!" %job_action)
                return True
            elif cluster_status.upper() in waitStatus:
                logger.warning("DI cluster %s status is %s!" %(job_action, cluster_status))
            else:
                logger.error("DI cluster %s status is %s ! Stop waiting when met this type of status!" %(job_action, cluster_status))
                return False
        else:
            logger.warning("Got unexpected status_code from server, status_code is %d, error information is %s" % (ret.status_code, ret.content))

        logger.warning("DI cluster %s is NOT Ready yet, wait another %d seconds!" % (job_action, check_interval))
        time.sleep(check_interval)

    logger.error("DI cluster %s timeout after %d seconds!" % (job_action, max_wait_ready_time))
    return False

def upgradeDIClusterByIM(owner,header,cluster_name):
    env = getEnv(cluster_name)
    result, _ = execAction(cluster_name, header, env)
    if not result:
        logger.error("Apply upgrade for cluster %s failed"  %cluster_name)
        return False, env
    if not waitStatusReady(owner, cluster_name, header, env):
        logger.error("DI cluster upgrade fail!")
        return False, env
    return True, env

def backupDIClusterByIM(owner,header,cluster_name):
    env = getEnv(cluster_name)
    result, backup_name = execAction(cluster_name, header, env)
    if not result:
        logger.error("Apply backup for cluster %s failed" %cluster_name)
        return False
    if not waitStatusReady(owner, cluster_name, header, env, BACKUP_NAME = backup_name):
        logger.error("DI cluster backup fail!")
        return False
    return True

def execAction(cluster_name, header, env):
    if job_action.upper() == 'UPGRADE':
        url = base_url + "/api/v1/tasks/upgrade/bdh/" + cluster_name
    elif job_action.upper() == 'BACKUP':
        url = base_url + "/api/v1/tasks/backup/" + cluster_name
    else:
        logger.info("Action: %s is not supported" % job_action)
        return False, None
    retry_num = 0
    while True:
        if job_action.upper() == 'UPGRADE':
            ret = runRequest(requests.post, url, json=env, headers=header)
        elif job_action.upper() == 'BACKUP':
            ret = runRequest(requests.post, url, headers=header)
        else:
            logger.error("Action: %s is not supported" % job_action)
            return False, None
        backup_name=''
        if ret.status_code == 200:
            data = ret.json()
            if job_action.upper() == 'BACKUP' and "output" in data:
                backup_name = data["output"]
                with open('/infrabox/output/backup_name.txt', 'w') as f:
                    f.write(backup_name)
            if data["status"] == "200":
                return True, backup_name
        else:
            logger.warning( "Got unexpected status_code from server, status_code is %d, error information is %s " % (ret.status_code, ret.content))
            retry_num = retry_num + 1
            if retry_num < max_error_retry_num:
                logger.info( "Wait for %d seconds and retry" % check_interval)
                time.sleep(check_interval)
            else:
                logger.error("Fail to %s cluster for  %d times!" % (job_action, max_error_retry_num))
                return False, None

def write_conf_file(cluster_name, header, admcfgFile=os.path.join('/infrabox', 'output', 'admin.conf'), data=None ):
    """
    get admin.conf file for given cluster_name
    :param cluster_name: the kubernetes cluster name
    :return: admin.conf file path
    """
    # get the admin.conf file
    if data is not None:
        with open(admcfgFile, 'w') as cfgfile:
            temp = data['kubecfg'].replace('\\n', '\n').replace('"', '')
            if temp.find('apiVersion') < 0 or temp.find('clusters') < 0 or temp.find('users') < 0:
                raise RuntimeError("The data in admin.conf is invalid for specified cluster_name %s" % cluster_name)
            cfgfile.write(temp)
            logger.info( "admin.conf file for kubernetes cluster %s is saved at %s" % (cluster_name, admcfgFile))
    else:
        url = '%s/api/v1/clusters/k8s/admcfg/%s' % (base_url, cluster_name)
        ret = runRequest(requests.get, url, headers=header)
        if ret.status_code == 200:
            data = ret.json()
            if 'adm_config' in data and data['adm_config'] is not None:
                config_data = data['adm_config']
                if config_data.find('apiVersion') < 0 or config_data.find('clusters') < 0 or config_data.find('users') < 0:
                    raise RuntimeError("The data in admin.conf is invalid for specified cluster_name %s" % cluster_name)
            else:
                raise RuntimeError("Failed to get adm_config data from specified cluster_name %s" % cluster_name)

            with open(admcfgFile, 'w') as cfgfile:
                temp = data['adm_config'].replace('\\n', '\n')
                cfgfile.write(temp)
                logger.info( "admin.conf file for kubernetes cluster %s is saved at %s" % (cluster_name, admcfgFile))
            if provision_platform.upper() == "GARDENER-CCLOUD":
                try:
                    f = open(admcfgFile,'r')
                    lines = f.readlines()
                    for line in lines:
                        if "name" in line:
                            shoot_name=line.split('--')[-1].replace('\n', '')
                            gardener_project_name=line.split('--')[-2].replace('\n', '')
                            break
                    if not os.path.exists('/infrabox/output/shoot_name.txt'):
                        with open('/infrabox/output/shoot_name.txt', 'w') as f:
                            f.write(shoot_name)
                    if not os.path.exists('/infrabox/output/gardener_project_name.txt'):
                        with open('/infrabox/output/gardener_project_name.txt', 'w') as f:
                            f.write(gardener_project_name)
                except RuntimeError as e:
                    logger.error("Fail to generate shoot_name file, error msg is: %s" % str(e))         
        else:
            raise RuntimeError("Fail to get admin.conf file from specified cluster_name %s" % cluster_name)        

    if provision_platform.upper() in ["MONSOON", "AWS-EKS"]:
        # get the hosts file
        url = '%s/api/v1/clusters/k8s/hosts/%s' % (base_url, cluster_name)
        ret = runRequest(requests.get, url, headers=header)
        if ret.status_code == 200:
            data = ret.json()
            hostsFile = os.path.join('/infrabox/output', 'hosts')
            with open(hostsFile, 'w') as hostsfile:
                hostsfile.write(data['hosts'])
                logger.info("hosts file for kubernetes cluster %s is saved at %s" % (cluster_name, hostsFile))
        else:
            raise RuntimeError("Fail to get hosts file from specified cluster_name %s" % cluster_name)

@timeout_decorator.timeout(int(os.environ.get("CREATE_TOTAL_TIMEOUT", 10800)))
def createK8sCluster(owner, header, tag="PUSH_VALIDATION"):
    """
    Apply for kubernetes environment, if failed, apply for max 3 times.

    return: cluster_name, url
    """
    max_create_retry_num = int(os.environ.get("MAX_CREATE_RETRY_NUM", 3))
    for i in range(max_create_retry_num):
        logger.info("-- Begin to create Kubernetes cluster for %d time --" % (i+1))
        try:
            cluster_name, url, bucket_name, shoot_name, env = applyForEnv(owner, header, tag, use_for, azure_registry_name)
        except timeout_decorator.timeout_decorator.TimeoutError:
            raise
        except RuntimeError as e:
            logger.error("Fail to apply for Kubernetes cluster, error msg is: %s" % str(e))
        else:
            # check for k8s cluster READY
            try:
                checkEnvReady(cluster_name, header, owner, env)
            except timeout_decorator.timeout_decorator.TimeoutError:
                raise
            except RuntimeError as e:
                logger.error("Kubernetes cluster creation failed!\n Error msg is: %s!\n Please check the build url for details: %s" % (str(e), url))
            else:
                logger.info("Kubernetes cluster creation succeed, the cluster %s is READY!" % cluster_name)
                return True, cluster_name, bucket_name, shoot_name, env

    return False, None, None, None, None

def getAuthHeader(owner):
    """
    Apply for auth header, if failed, apply for max 3 times.

    return: header
    """
    if 'IM_AUTH_HEADER' in os.environ:
        token = os.environ['IM_AUTH_HEADER']
        return {'Authorization': 'Bearer {}'.format(token)}
    else:
        SYS_ACCOUNT = os.environ.get('SYS_ACCOUNT')
        SYS_PASSWORD = os.environ.get('SYS_PASSWORD')
        if SYS_ACCOUNT is None or SYS_PASSWORD is None:
            raise RuntimeError("Fail to generate auth header, no SYS_ACCOUNT or SYS_PASSWORD!")

        response = runRequest(requests.post, base_url + '/api/v1/users/user/' + owner, data=json.dumps({"username":SYS_ACCOUNT,"password":SYS_PASSWORD}))
        # try both /api/v1/users/user/ and /api/v1/user/ for backward capability
        if response.status_code != 200:
            response = runRequest(requests.post, base_url + '/api/v1/user/' + owner, data=json.dumps({"username":SYS_ACCOUNT,"password":SYS_PASSWORD}))
        if response.status_code != 200: #pylint: disable=no-else-raise
            logger.error("Can not get auth token, API server respond error!")
            raise RuntimeError("Fail to genreate auth header!")
        else:
            token = response.json().get('token')
            return {'Authorization': 'Bearer {}'.format(token)}

def getNamespace(cluster_name, header, owner):
    """
    get namespace file for given cluster_name
    :param cluster_name: the kubernetes cluster name
    :return:
    """
    # get the namespace file
    url=base_url+'/api/v1/tasks/deployment/'+owner+'?page=1&per_page=10&kc_name='+cluster_name
    ret = runRequest(requests.get, url, headers=header)
    if ret.status_code == 200:
        data = ret.json()

        tasks=data['tasks']
        tasks=json.loads(tasks)
        namespace = None
        if 'K8S_INSTALLER_NAMESPACE' in tasks[0]['kc_dply_cfg']['environment']:
            namespace = tasks[0]['kc_dply_cfg']['environment']['K8S_INSTALLER_NAMESPACE']
        else: #dhaas
            namespace = tasks[0]['kc_dply_cfg']['environment']['CLUSTER']['installationMetadata']['namespace']

        logger.info("get cluster namespace: " + namespace)

	# write a file k8s_namespace.txt with namespace
        with open('/infrabox/output/k8s_namespace.txt', 'w') as f:
            f.write(namespace)
        return namespace
    else:
        raise RuntimeError("Fail to get namespace file from specified cluster_name %s" % cluster_name)

# pylint: disable=inconsistent-return-statements
def getK8sVersion(url, header, major_version):
    response = runRequest(requests.get, url, headers=header)
    if response.status_code != 200:
        logger.error("Cannot get avaliable k8s list by url: %s" % url)
        return None
    else:
        versions = response.json().get('versions')
        major_version_filter = list(filter(lambda versions: major_version in versions, versions)) # pylint: disable=bad-option-value, deprecated-lambda
        if major_version_filter:
            minor_list = []
            tiny_list = []
            versions_with_same_minor = []
            # get the highest minor version x. eg: 1.11.x-gke
            for i in range(len(major_version_filter)):
                if '-' in major_version_filter[i]: #pylint: disable=unsubscriptable-object
                    minor_list.append(int(re.search(r'.(\d+)-', major_version_filter[i]).group(1))) #pylint: disable=unsubscriptable-object
                else:
                    # match 1.11.x only
                    minor_list.append(int(re.search(r'.(\d+)$', major_version_filter[i]).group(1))) #pylint: disable=unsubscriptable-object
            highest_minor_version = max(minor_list)
            # get the highest tiny version y. eg: 1.11.9-gke.y
            for i in range(len(minor_list)):
                if minor_list[i] == highest_minor_version:
                    versions_with_same_minor.append(major_version_filter[i]) #pylint: disable=unsubscriptable-object
            for i in range(len(versions_with_same_minor)):
                if 'gke' in versions_with_same_minor[i]:
                    tiny_list.append(int(re.search(r'gke.(\d+)', versions_with_same_minor[i]).group(1)))
            if len(tiny_list) > 0:
                highest_tiny_version = max(tiny_list)
                for i in range(len(tiny_list)):
                    if tiny_list[i] == highest_tiny_version:
                        return versions_with_same_minor[i]
            else:
                return versions_with_same_minor[0]
        else:
            logger.error("Cannot get %s k8sVersion ,please check avaliable k8s version" % major_version)
            exit(1)

# pylint:disable=lost-exception
def getEksK8sVersion(eks_region, header, major_version):
    url = '%s/api/v1/configs/versions/k8s/AWS-EKS/%s' % (base_url, eks_region)
    response = runRequest(requests.get, url, headers=header)
    if response.status_code != 200:
        logger.error("Cannot get avaliable k8s list by url: %s" % url)
        return None, None
    versions = set()
    eksVersions = response.json()
    try:
        for item in eksVersions["versions"]:
            # pylint:disable=pointless-string-statement
            """
            An item looks like:
            {
                "Description": "EKS Kubernetes Worker AMI with AmazonLinux2 image (k8s: 1.13.7, docker:18.06)",
                "ImageId": "ami-09bbefc07310f7914",
                "Version": "k8s: 1.13, AMI Name: amazon-eks-node-1.13-v20190614 with DH installation verified"
            },
            """
            version = item["Version"].split(",")[0].split('k8s: ')[1]
            #only keep 2 parts of version. e.g. if read a version looks like '1.12.x', save '1.12'
            versions.add(float('.'.join(version.split('.')[:2])))
    except Exception as e:
        logger.error(str(e))
    finally:
        vers = (major_version, None)
        versions = [str(x) for x in sorted(list(versions))]
        version_list_len = len(versions)
        if version_list_len == 1 and major_version != versions[0]:
            vers = (versions[0], None)
        if version_list_len > 1:
            if major_version not in versions:
                vers = (versions[0], versions[1])
            else:
                position = versions.index(major_version)
                if position == version_list_len - 1:
                    #major_version is the highest version in avliable version list, need to check if it was upgrade test
                    if upgrade_test == "yes":
                        vers = (versions[-2], versions[-1])
                else:
                    vers = (major_version, versions[position + 1])
        return vers

def get_header():
    header = None
    enableHeader = os.environ.get("ENABLE_AUTH_HEADER", "yes")
    if enableHeader.upper() == "YES":
        # generate auth header
        header = getAuthHeader(owner)
        headerStr = "Authorization: " + header['Authorization']
        logger.info("Auth header: %s" % headerStr)
        # write auth header to file
        with open('/infrabox/output/auth_header.txt', 'w') as f:
            f.write(headerStr)
    return header

def update_k8s_version():
    # For on_premise: Support set k8s_version from infrabox env, 
    if "K8S_VERSION" in os.environ and os.environ["K8S_VERSION"]:
        env_aks_model["environment"]["K8S_VERSION"] = os.environ["K8S_VERSION"]
        env_gke_model["environment"]["K8S_VERSION"] = os.environ["K8S_VERSION"]
        env_eks_model["environment"]["K8S_VERSION"] = os.environ["K8S_VERSION"]

    if provision_platform.upper() == "GKE":
        url = '%s/api/v1/configs/versions/k8s/GCP-GKE/%s/%s' % (base_url,
                                                                env_gke_model["environment"]["GCP_PROJECT_ID"],
                                                                env_gke_model["environment"]["GCP_ZONE"])
        if "GCLOUD_RELEASE_CHANNEL" in os.environ and os.environ["GCLOUD_RELEASE_CHANNEL"]:
            env_gke_model["environment"]["GCLOUD_RELEASE_CHANNEL"] = os.environ["GCLOUD_RELEASE_CHANNEL"]
        if env_gke_model["environment"]["GCLOUD_RELEASE_CHANNEL"] != "static":
            url += '/' + env_gke_model["environment"]["GCLOUD_RELEASE_CHANNEL"]
        avaliable_k8s_ver = getK8sVersion(url, header, env_gke_model["environment"]["K8S_VERSION"])

        if avaliable_k8s_ver is not None:
            env_gke_model["environment"]["K8S_VERSION"] = avaliable_k8s_ver
    elif provision_platform.upper() == "AZURE-AKS":
        if 'AKS_SUBSCRIPTION_NAME' in os.environ:
            url = '%s/api/v1/configs/versions/k8s/AZURE-AKS/%s/%s' % (base_url, os.environ["AKS_SUBSCRIPTION_NAME"], env_aks_model["environment"]["AZURE_RESOURCE_LOCATION"])
        else:
            url = '%s/api/v1/configs/versions/k8s/AZURE-AKS/%s' % (base_url, env_aks_model["environment"]["AZURE_RESOURCE_LOCATION"])
        avaliable_k8s_ver = getK8sVersion(url, header, env_aks_model["environment"]["K8S_VERSION"])

        if avaliable_k8s_ver is not None :
            env_aks_model["environment"]["K8S_VERSION"] = avaliable_k8s_ver
    elif provision_platform.upper() == "AWS-EKS":
        # use fixed EKS_WORKER_NODES_IMAGE_ID
        # contact IM team for the value in other region or k8s 1.15+,
        avaliable_k8s_ver, available_k8s_upgrade_ver = getEksK8sVersion(env_eks_model["environment"]["EKS_AWS_REGION"],
                                                                        header, env_eks_model["environment"]["K8S_VERSION"])
        if avaliable_k8s_ver is not None:
            env_eks_model["environment"]["K8S_VERSION"] = avaliable_k8s_ver
        if available_k8s_upgrade_ver is not None and upgrade_test == "yes":
            with open('/infrabox/output/k8s_upgrade_to.txt', 'w') as f:
                f.write(available_k8s_upgrade_ver)

def excute_job_action():
    # create k8s cluster
    cluster_name = None
    env = None
    result = False
    if job_action.upper() == 'CREATE':
        result, cluster_name, bucket_name, shoot_name, env = createK8sCluster(owner, header, tag)
        if bucket_name is not None:
            with open('/infrabox/output/k8s_bucket.txt', 'w') as f:
                f.write(bucket_name)
        if shoot_name is not None:
            with open('/infrabox/output/shoot_name.txt', 'w') as f:
                f.write(shoot_name)
    elif job_action.upper() == 'HIBERNATE':
        cluster_name = os.environ.get("K8S_CLUSTER_NAME")
        result = hibernateWakeupCluster(owner, cluster_name, header, pods_number=0)
    elif job_action.upper() == 'WAKEUP':
        cluster_name = os.environ.get("K8S_CLUSTER_NAME")
        result = hibernateWakeupCluster(owner, cluster_name, header, pods_number=os.environ.get("CLUSTER_PODS_NUM", 3))
    else:
        provision_platform = os.environ.get("PROVISION_PLATFORM")
        if not provision_platform.upper().startswith("DHAAS-"):
            logger.error( provision_platform + ' is not a DI cluster, ' + job_action + ' is not supported')
            exit(1)
        cluster_name = os.environ.get("K8S_CLUSTER_NAME")
        if job_action.upper() == 'RESTORE':
            result, cluster_name, env = restoreDIClusterByIM(owner, header, cluster_name)
        elif job_action.upper() == 'BACKUP':
            result = backupDIClusterByIM(owner,header,cluster_name)
        elif job_action.upper() == 'UPGRADE':
            result, env = upgradeDIClusterByIM(owner,header,cluster_name)
        else:
            logger.error('Unknown action: %s' %job_action)

    return result, cluster_name, env

def export_files(cluster_name, header, env):
    with open('/infrabox/output/k8s_cluster.txt', 'w') as f:
        f.write(cluster_name)

    if env is not None:
        with open('/infrabox/output/k8s_version.txt', 'w') as f:
            f.write(env["environment"]["K8S_VERSION"])

        with open('/infrabox/output/hdfs_whiltelist_info.sh', 'w') as f:
            if 'ADD_INTO_FIREWALL_WHITELIST' in env['environment'] and \
                    env['environment']['ADD_INTO_FIREWALL_WHITELIST'] == 'yes':
                f.write("export ADD_INTO_FIREWALL_WHITELIST=yes")
            else:
                f.write("export ADD_INTO_FIREWALL_WHITELIST=no")

    write_conf_file(cluster_name, header)

    if check_datahub_installed():
        namespace = getNamespace(cluster_name, header, owner)
        with open(bdh_base_version_file, 'a+') as f:
            f.write("export NAMESPACE=" + str(namespace + '\n'))
        if 'BASE_BDH_VERSION' in os.environ:
            with open(bdh_base_version_file, 'a+') as f:
                f.write("export BASE_BDH_VERSION=" + str(os.environ.get("BASE_BDH_VERSION") + '\n'))

    if provision_platform.upper() == "AZURE-AKS":
        with open('/infrabox/output/k8s_info.sh', 'w') as f:
            azure_registry_name, azure_resource_group = getAKSClusterResourceInfo(cluster_name, header)
            f.write("export AZURE_REGISTRY_NAME=" + azure_registry_name)
            f.write("\nexport AZURE_RESOURCE_GROUP=" + azure_resource_group)
            if 'AKS_SUBSCRIPTION_NAME' in os.environ:
                f.write("\nexport AKS_SUBSCRIPTION_NAME=" + os.environ['AKS_SUBSCRIPTION_NAME'])


def checkCentralMonitor(im_central_monitor_url, env_im_central_monitor_model):
    """
    Status check in Central Monitor
    if env_im_central_monitor_model.value set to True, raise error and return False
    if env_im_central_monitor_model.value set to False, only raise warning, by pass the status check
    """

    flag = True
    result_dict = {}

    try:
        ret = runRequest(requests.get, im_central_monitor_url)
        if ret.status_code == 200:
            connecions_status = json.loads(ret.content)
            #loop each item of env_im_central_monitor_model
            for connection_data in connecions_status['data']:
                if connection_data['name'] in env_im_central_monitor_model['general']:
                    check_value = env_im_central_monitor_model['general'][connection_data['name']] 
                elif connection_data['name'] in env_im_central_monitor_model[provision_platform.upper()]:
                    check_value = env_im_central_monitor_model[provision_platform.upper()][connection_data['name']]
                else:
                    continue 
                if connection_data['status_name'] == 'Operational':
                    logger.info("Central Monitor: %s status check successful" %(connection_data['name']))
                else:
                    if check_value:
                        logger.error("### [level=error] Central Monitor: %s status check failed, the status is %s" % (connection_data['name'], connection_data['status_name']))
                        flag = False
                    else:
                        logger.warning("### [level=warning] Central Monitor: %s status check failed, the status is %s" % (connection_data['name'], connection_data['status_name']))
                result_dict[connection_data['name']] = connection_data['status_name']       
        else:
            logger.warning("### [level=warning] Central Monitor: %s can not work well, error code: %d, by pass the status check." % (im_central_monitor_url, ret.status_code))
    except Exception as e:
        logger.warning("### [level=warning] Central Monitor: status check in %s failed with error message %s, by pass the status check." % (im_central_monitor_url, e))
    finally:
        # output all status
        result_json = json.dumps(result_dict, indent=1)
        logger.info("Central Monitor Result List: \n{}".format(result_json))

        return flag  # pylint:disable=lost-exception

if __name__ == "__main__":
    logger = init_logger('/infrabox/output/create_k8s_cluster.log')

    use_for = str(os.environ.get("USE_FOR", ""))
    tag = os.environ.get("USE_FOR", "PUSH_VALIDATION")
    owner = os.environ.get("OWNER", "SDHINFRA")
    azure_registry_name = get_azure_registry_name()
    vora_version = os.environ.get('VORA_VERSION', None)
    gerrit_branch = os.environ.get('GERRIT_CHANGE_BRANCH', None)

    # set k8s_version to 1.26 for rel-3.3
    if vora_version is not None and (vora_version.startswith("3.3") or gerrit_branch == "rel-3.3"):
        env_gke_model["environment"]["K8S_VERSION"] = "1.26"
        env_aks_model["environment"]["K8S_VERSION"] = "1.26"

    if upgrade_test == "yes":
        update_env_when_upgrade()
    # set single node for push validation
    if use_for == 'PUSH_VALIDATION' and upgrade_test != "yes":
        env_gke_model["environment"]["GCP_MACHINE_TYPE"] = "n1-standard-8"
        env_gke_model["environment"]["NUMBER_OF_WORKERS"] = "3"
        env_dhaas_aws_model["environment"]["NUMBER_OF_WORKERS"] = "1"
        env_dhaas_azure_model["environment"]["NUMBER_OF_WORKERS"] = "1"
    if use_for == 'MILESTONE_VALIDATION':
        env_dhaas_aws_model["environment"]["NUMBER_OF_WORKERS"] = "3"
        env_dhaas_azure_model["environment"]["NUMBER_OF_WORKERS"] = "3"
    if use_for == 'AUTO_ENV':
        update_env_for_auto_env()
    header = get_header()

    # check Quata
    loop = 0
    while (checkQuota(header) != 0) & (loop < max_error_retry_num):
        logger.info("Check the quotas after %s seconds" % check_interval*5)
        time.sleep(check_interval*5)
        loop += 1

    if use_for == 'PUSH_VALIDATION':
        logger.info("PUSH_VALIDATION: Central Monitor: check status")
        central_monitor_result = checkCentralMonitor(im_central_monitor_url, env_im_central_monitor_model)
        if not central_monitor_result:
            logger.error("### [level=warning] Central Monitor: Check status failed.")
            exit(1)

    update_k8s_version()

    result, cluster_name, env = excute_job_action()
    if not result:
        exit(1)

    if job_action.upper() == 'HIBERNATE' \
            or job_action.upper() == 'WAKEUP' \
            or job_action.upper() == 'BACKUP':
        exit(0)
    else:
        export_files(cluster_name, header, env)
