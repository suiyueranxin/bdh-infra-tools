Integrate New Infrabox Validation Job
=======
# Prepare a Dockerfile 

The Docker file is the entry for the validation tests.

The CI will build the docker file and run it as single infrabox validation job.

You could address the docker build arguments and docker run enviroments, so the CI will append these options with docker build and docker run. See [Prepare other infomation](#prepare-other-infomation)

## How to connect to the Datahub
The CI(Continuous Integration) will mount `/infrabox` folder with docker run and also append an enviroment named `ENV_FILE` which is a file path that contains the enviroments that could be used to connect DH.
So a typical docker file should contain an ENTRYPOINT *bash* script at the end and ```source $ENV_FILE``` before the test running.

__Optional__ You could also run this command in *bash*  directly ```export VORA_ENV_FILE=$(find /infrabox/inputs -mindepth 2 -maxdepth 2 -name env.sh); source $VORA_ENV_FILE```

The value of `ENV_FILE` would be like `/infrabox/inputs/install_{platform}/env.sh`

The content of `ENV_FILE` would be like below:

```
export VORA_VERSION=2.6.25
export GERRIT_CHANGE_BRANCH=master
export ALL_COMPONENTS_VERSIONS='{"hl-vsystem-ui": "2.6.6", "security-operator": "2.6.12", "sapjvm": "81.34.34", "datahub-flowagent": "2.6.18", "dsp-release": "0.2.13", "hl-data-tools-ui": "2.6.17", "storagegateway": "2.6.3", "consul": "0.9.0-sap23", "hl-vora-tools": "2.6.4", "hl-vsystem": "2.6.20", "hl-vsolution": "2.6.27", "hl-spark-datasources": "2.6.5", "hl-hana-replication": "0.0.78", "hl-lib": "2.6.23", "docker-base": "15.0-sap11", "hl-ui-components": "2.6.6", "datahub-license-manager": "2.6.9", "datahub-app-base": "2.6.21"}'
export VSYSTEM_VERSION=2.6.20
export APP_BASE_VERSION=2.6.21
export FLOWAGENT_VERSION=2.6.18
export LICENSE_MANAGER_VERSION=2.6.9
export HANALITE_LIB_VERSION=2.6.23
export SECURITY_OPERATOR_VERSION=2.6.12
export SAPJVM_VERSION=81.34.34
export DATA_TOOLS_UI_VERSION=2.6.17
export SPARK_DATASOURCES_VERSION=2.6.5
export VSYSTEM_UI_VERSION=2.6.6
export UI_COMPONENTS_VERSION=2.6.6
export VORA_TOOLS_VERSION=
export CONSUL_VERSION=0.9.0-sap23
export HANA_REPLICATION_VERSION=0.0.78
export VFLOW_VERSION=2.6.4
export VSOLUTION_VERSION=2.6.27
export VORA_TENANT="default"
export VORA_USERNAME="system"
export VORA_SYSTEM_TENANT_PASSWORD="bDh17@Objth"
export VORA_PASSWORD="bDh59@kamsS"
export PROVISION_PLATFORM="GKE"
export NODE_HOST="35.204.174.133"
export VSYSTEM_PORT="30084"
export VSYSTEM_ENDPOINT="https://lily-ke-20190409-220521322-gke.infra.datahub.sapcloud.io:443"
export NAMESPACE="vora-nightly-293-1"
export KUBECONFIG="/infrabox/inputs/k8s_creation_gke/admin.conf"
export K8S_VERSION="1.11.8-gke.6"
export K8S_CLUSTER_NAME="lily-ke-20190409-220521322"
export CONTAINER_REGISTRY_ADDRESS="eu.gcr.io/sap-p-and-i-big-data-vora/lily-ke-20190409-220521322"
export GCP_DOCKER_REGISTRY_SUFFIX=lily-ke-20190409-220521322
```
__NODE_HOST__ only avaliabe for GKE platform. For other platforms it would be same as the *VSYSTEM_ENDPOINT* but without port number

__VSYSTEM_PORT__ only avaliabe for GKE platform. For other platforms it is _443_.

__VORA_SYSTEM_TENANT_PASSWORD__ is for _system_ tenant user.

__VORA_PASSWORD__ is for the *VORA_TENANT* user.

__KUBECONFIG__ is the file path for the k8s credentials, you could use it directly in your contianer.

## Version
There are also components version information in `ENV_FILE`. The CI will checkout the test repository by the components version tag, eg: `rel/2.6.27`

## Save the test result
You could copy the log files directly into this folder: __/infrabox/upload/archive/__ then it could be downloaded from the __ARCHIVE__ page of infrabox job.

You could also save the test result file to __/infrabox/upload/testresult/__ to have a better view of the test case status from the __TESTS__ page. The result files must be in [junit xml format](https://www.ibm.com/support/knowledgecenter/en/SSUFAU_1.0.0/com.ibm.rsar.analysis.codereview.cobol.doc/topics/cac_useresults_junit.html).

# Prepare other infomation
To register a new job. You need prepare the following:
*   What’s the validation test job name ?

     *eg: vflow_ui_e2e_test*
*   Which Component name should be used in the Bugzilla when the job failed?  

     *eg: Vora Tools and UIs*
*   Which component name string listed in the `ENV_FILE`could be used to check out the repository?

    *eg: VSYSTEM_UI_VERSION*
*   Docker file path

     *eg: https://github.wdf.sap.corp/velocity/data-tools-ui/blob/master/Dockerfile*
*   Directory to build the docker file

     *eg:  build the docker file in the root folder of repository https://github.wdf.sap.corp/velocity/data-tools-ui/*
*   Is there any other arguments or options for your docker build or docker run ? 

    *eg: for docker build EXTRA_ARG=vsystem_ui. for docker run TEST_SCENARIO="scenario1"*

     _Note_: the docker run options could be update later from the [json file](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/refs/heads/master/TestCycleConfiguration/TestPlans.json)
*   How long it would take? The default timeout is 1 hour. 

     *eg: less than 30 mins*


# Prepare a Docker Image [optional]
If you could push the test docker image with component version tag to a registry when tag the repository. The CI could also run it directly.

eg: for __LICENSE_MANAGER__ public.int.repositories.cloud.sap/com.sap.datahub.linuxx86_64/test-vora-license-manager:*2.5.20*

