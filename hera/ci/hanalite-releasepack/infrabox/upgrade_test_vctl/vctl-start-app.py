import os
import json
import subprocess
import re
import requests
import time
from random import randint

endpoint = str(os.getenv("VSYSTEM_ENDPOINT"))
tenant = str(os.getenv("VORA_TENANT"))
username = str(os.getenv("VORA_USERNAME")) + " "
password = str(os.getenv("VORA_PASSWORD"))
systemPassword = str(os.getenv("VORA_SYSTEM_TENANT_PASSWORD"))
registryAddress = str(os.getenv("CONTAINER_REGISTRY_ADDRESS"))
bdhVersion = str(os.getenv("VORA_VERSION")).split(".")
namespace = str(os.getenv("DI_NAMESPACE"))
platform = str(os.getenv("PROVISION_PLATFORM"))
listApps = "vctl util http /scheduler/v2/template"
listTenants = "vctl tenant list"
listStrategy = "vctl strategy list"
getRegistry = "vctl parameter get vsystem.registry"


def get_strategy(tenant_name):
    # skip "-ms" part of the version tag
    # If the VORA_VERSION doesn't contain -ms, it still work.
    dh_version = str(os.getenv("VORA_VERSION")).split("-")[0]
    return "strat-{}-{}".format(tenant_name, dh_version)


def login(tenant_name, user_name, password):
    print "\n*** Trying to login with the %s tenant %s user %s password ***\n" % (tenant_name, user_name, password)
    space = " "
    procs = os.system(
        "vctl login " + endpoint + space + tenant_name + space + user_name + space + "-p \'" + password + "\' --insecure")
    if procs == 0:
        print "\n*** Login with the %s tenant is successfull ***\n" % (tenant_name)
    else:
        raise Exception("\n*** Login with the tenant is not successfull ***")


def create_new_tenant():
    global testTenant
    login("system", "system", systemPassword)
    p = subprocess.Popen(listTenants, stdout=subprocess.PIPE, shell=True)
    data = p.stdout.read()
    for test in data.split("\n"):
        if "test-tenant" in test:
            deleteTenant = os.system(
                "vctl tenant delete %s" % test.split(" ")[0])  # deletes all tenant start with test-tenant
            if deleteTenant == 0:
                print "\n*** Previous tenants deleted successfully ***\n"
            else:
                raise Exception("\n*** Delete tenant is not successfull ***")
    testTenant = "test-tenant%d" % randint(1000, 9999)
    newTenant = os.system("vctl tenant create %s" %
                          testTenant)  # creates new tenant
    if newTenant == 0:
        print "\n*** Tenant created successfully ***\n"
    else:
        raise Exception("\n*** Tenant creation is not successfull ***")


def create_new_user():
    global newUserName
    global generatePassword
    newUserName = "test-user%d" % randint(1000, 9999)
    generatePassword = "Test%d!" % randint(100, 999)
    newUser = os.system("vctl user create %s %s %s tenantAdmin" %
                        (testTenant, newUserName, generatePassword))
    if newUser == 0:
        print "\n*** User created successfully ***\n"
    else:
        raise Exception("\n*** User creation is not successfull ***")

def set_strategy_back_for_default_tenant():
    login("system", "system", systemPassword)
    os.system("vctl tenant set-strategy default sdi-default-extension-strategy" )

def set_new_strategy_to_tenant(tenant_name, strategy_name):
    p = subprocess.Popen(listStrategy, stdout=subprocess.PIPE, shell=True)
    data = p.stdout.read()
    data = data.split("\n")
    strategy = get_strategy(strategy_name)
    print "\n*** Setting tenant %s to the %s strategy ***\n" % (tenant_name, strategy)
    setStrategy = -1
    for strat in data:
        if strategy in strat:
            setStrategy = os.system(
                "vctl tenant set-strategy %s %s" % (tenant_name, strategy))
            if setStrategy == 0:
                print "\n*** New strategy is set successfully to the tenant %s***\n" % (tenant_name)
            else:
                raise Exception("\n*** Strategy assignment failed ***")
            break
    if setStrategy == -1:
        raise Exception("\n*** New strategy could not be found ***")

    if tenant_name == "system":
        print "\n*** New strategy was assigned to the system tenant. All aplications in the cluster have to be stopped. ***\n"
        for count in range(1, 12):
            # stop all apps in the cluster
            stopCluster = os.system("vctl scheduler stop --all")
            if stopCluster == 0:
                print "\n*** Stopped all applications in the cluster ***\n"
                break
            elif count == 11:
                raise Exception(
                    "\n*** Couldn't stop all aplications in the cluster***")
            else:
                print "Failed to stop all applications at %d try" % (count)


def set_vflow_registry_secret(tenant_name):
    print "\n*** Create vflow-registry secret. ***\n"
    reg_address = os.getenv("CONTAINER_REGISTRY_ADDRESS")
    reg_user_name = os.getenv("CONTAINER_REGISTRY_USERNAME")
    reg_user_pass = os.getenv("CONTAINER_REGISTRY_PASSWORD")
    import tempfile
    new_file, filename = tempfile.mkstemp()

    secret = "- address: {0}\n  username: {1}\n  password: {2}".format(
        reg_address, reg_user_name, reg_user_pass)

    os.write(new_file, secret)
    print "\n*** Running \"vctl secret create vflow-secret --filename \"%s\" \" ***" % (filename)
    createSecret = os.system(
        "vctl secret create vflow-registry --filename \"{0}\"".format(filename))
    os.close(new_file)
    if createSecret == 0:
        print "\n*** New vflow-registry secret is created successfully***\n"
        set_vctl_vflow_registry_secret("vflow-registry")
    else:
        raise Exception("\n*** Vflow-registry secret creation failed ***")

def set_vflow_secret(tenant_name):
    print "\n*** Create vflow-secret secret file. ***\n"
    filename = "vflow-secret-content.yaml"
    getSecret = os.system(
        "kubectl -n datahub get secret vflow-secret -o jsonpath='{.data.secret}' | base64 -d > vflow-secret-content.yaml")
    login("system", "system", systemPassword)
    createSecret = os.system(
        "vctl secret create vflow-secret --filename \"{0}\"".format(filename))
    if createSecret == 0:
        print "\n*** New vflow-secret secret is created successfully***\n"
        set_vctl_vflow_registry_secret("vflow-secret")
    else:
        raise Exception("\n*** vflow-secret secret creation failed ***")
    login(testTenant, newUserName, generatePassword)

def set_vctl_vflow_registry_secret(secret_name):
    if platform == "DHAAS-AWS":
        login("system", "system", systemPassword)
    setSecret = os.system(
            "vctl parameter set vflow.registrySecret {0}".format(secret_name))
    if setSecret == 0:
        print ("\n*** {0} secret was set successfully***\n".format(secret_name))
    else:
        raise Exception("\n*** {0} secret could not be set ***".format(secret_name))
    if platform == "DHAAS-AWS":    
        login(testTenant, newUserName, generatePassword)

def get_configmap(config_file, namespace):
    procs = os.system("kubectl get -n " + namespace + " cm vsystem-configmap -o yaml >" + config_file)
    if procs == 0:
        print "\n*** Successfuly received %s config file ***\n"% (config_file)
    else:
        raise Exception("\n*** Could not get config file ***")


def update_configmap(config_file):
    lines = []
    count = 0
    with open(config_file, 'r') as f:
        for line in f:
            lines.append(line)
            # add line only once
            if "VSYSTEM_DATALAKE_ADDRESS" in line and count != 1:
                lines.append("  SUBACCOUNT_ID_FROM_DEPLOYMENT_INFO: \"true\"\n")
                count = count + 1

    with open(config_file, 'w') as f:
        for line in lines:
            f.write(line)


def apply_configmap(namespace, config_file):
    procs = os.system("kubectl apply -n " + namespace + " -f " + config_file)
    if procs == 0:
        print "\n*** Successfuly applied %s config file ***\n" % (config_file)
    else:
        raise Exception("\n*** Could not apply config file ***")


def restart_vsystem(namespace):
    procs = os.system("kubectl rollout -n " + namespace + " restart deployment vsystem")
    if procs == 0:
        print "\n*** Successfuly restarted vsystem ***\n"
        print "\n*** Waiting for vsystem to start ***\n"
        time.sleep(1)
        count = 0
        ready = False
        while(not ready and count < 10):
            p = subprocess.Popen("kubectl -n " + namespace + " get po -l datahub.sap.com/app-component=vsystem | awk 'NR==2 { print $3 }'", stdout=subprocess.PIPE, shell=True)
            status = p.stdout.read()
            print(status)
            if "Running" not in status:
                time.sleep(1)
                count = count + 1
            else:
                ready = True
                break
        
        if not ready:
            raise Exception("\n*** Vsystem couldn't be started after restart ***")
    else:
        raise Exception("\n*** Could not restart vsystem ***")



def add_subaccountid_ff(namespace):
    config_file = "vsystem-config.yaml"
    get_configmap(config_file, namespace)
    update_configmap(config_file)
    apply_configmap(namespace, config_file)
    restart_vsystem(namespace)


def check_version():
    r = requests.get(endpoint + "/service/v2/version/")
    if r.status_code != 200:
        raise Exception("\n*** Could not retrieve version information ***")

    data = r.json()

    if 'deploymentType' in data:
        # sapaccountid is only activated for DHaaS systems
        if data["deploymentType"] == "DHaaS":
            if "version" in data:
                version = data["version"].split(".")
                version_major = int(version[0])
                version_minor = int(version[1])
                # sapaccountid is only activated for systems after 2110.2 milestone
                if version_major > 2110 or (version_major == 2110 and version_minor >= 2):
                    return True
    
    return False


def check_tenant_info(tenant_name):
    p = subprocess.Popen("vctl util http -X GET '/api/tenant-management/v3/tenants/" + tenant_name + "'", stdout=subprocess.PIPE, shell=True)
    tenant_data = p.stdout.read().decode('utf8')
    tenant_json = json.loads(tenant_data)

    if "subAccountId" in tenant_json:
        print "\n*** SubAccountId was set successfuly %s ***\n" % (tenant_json["subAccountId"]) 
    else:
        print "\n*** The following tenant information was returned %s ***\n" % (json.dumps(tenant_json, indent = 1)) 
        raise Exception("\n*** Could not retrieve subAccountId ***")


def launch_apps():
    version = bdhVersion[0] + bdhVersion[1] + bdhVersion[2]
    version = re.split("[-]", version)
    if len(version[0]) < 4:
        version[0] += "0"
    if int(version[0]) < 2471:
        setRegistry = os.system(
            "vctl parameter set vflow.registry %s" % registryAddress)
        if setRegistry == 0:
            print "\n*** Docker registry set is successfull: %s ***\n" % registryAddress
        else:
            raise Exception("\n*** Docker registry set is not successfull ***")
    p = subprocess.Popen(listApps, stdout=subprocess.PIPE, shell=True)
    data = p.stdout.read()
    data = json.loads(data)
    for i in data:
        if i["type"] == "link":
            # skipping test: link apps cannot be started and stopped
            continue
        id = i["id"]
        space = i["space"]
        for count in range(1, 21):
            procs = os.system("vctl scheduler start %s" % id)
            if procs == 0:
                print "\n*** %s started successfully at %d th try ***\n" % (i["name"], count)
                if "license-manager" in id:
                    print "license-manager can only be stopped from cluster-admin -- skipping stop\n"
                else:
                    stopApp = os.system("vctl scheduler stop %s" % id)
                    if stopApp == 0:
                        print "*** %s has stopped successfully" % i["name"]
                    else:
                        print "%s failed to stop" % i["name"]
                break
            elif count == 20:
                raise Exception("%s failed to start" % i["name"])
            else:
                print "Failed to start %s at %d th try" % (i["name"], count)


def delete_tenant():
    login("system", "system", systemPassword)
    p = subprocess.Popen(listTenants, stdout=subprocess.PIPE, shell=True)
    data = p.stdout.read()
    for test in data.split("\n"):
        if "test-tenant" in test:
            deleteTenant = os.system(
                "vctl tenant delete %s" % test.split(" ")[0])  # deletes all tenant start with test-tenant
            if deleteTenant == 0:
                print "\n*** Newly created test tenant deleted successfully ***\n"
            else:
                raise Exception("\n*** Delete tenant is not successfull ***")


if __name__ == '__main__':
    # no need to set new strategy to system tenant as it is part of the upgrade procedure
    create_new_tenant()
    set_new_strategy_to_tenant("default", "default")
    create_new_user()
    set_new_strategy_to_tenant(testTenant, "default")
    login(testTenant, newUserName, generatePassword)

    set_vflow_registry_secret(testTenant)
    # only add the vflow-secret in DHAAS-AWS for now, It will read the vflow-secret in default tenant, and upload to non-default tenant
    # can't run this in on-prem cluster because no vflow-secret file in on-prem cluster.
    if platform == "DHAAS-AWS":
        set_vflow_secret(testTenant)
    launch_apps()
    delete_tenant()
    set_strategy_back_for_default_tenant()

    # check whether subaccountid is supported
    if check_version():
        login(tenant, username, password)
        add_subaccountid_ff(namespace)
        time.sleep(20) # sleep 20 seconds to wait for the restart vsystem to avoid the login failed.
        login("system", "system", systemPassword)
        check_tenant_info(tenant)
    else:
        print "\n*** The current version does not support subAccountId. Checks will be skipped. ***\n"

