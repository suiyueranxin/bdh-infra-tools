#!/usr/bin/env bash
set -x
if [ -n "${PARENT_INSTALL_JOB}" ]; then
  if [ ! -f /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh ]; then
    echo "/infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh does not exist. Skip the current job"
    exit 0
  else
    source /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh
  fi
else
  echo "## Skip sourcing env.sh, Using external env information..."
fi

source /project/common.sh
echo "## Start vflow testing..."
LOG_OUTPUT_DIR="/infrabox/output/execution_log/vflow"
mkdir -p $LOG_OUTPUT_DIR
echo $NAMESPACE

download_vctl

kubectl version
GIT_SSL_NO_VERIFY=1
git config --global http.sslVerify false

echo '## Clone vFlow'
git clone --single-branch --branch rel/$VFLOW_VERSION git@github.wdf.sap.corp:velocity/vflow.git
if [ $? != 0 ]; then
  cat << EOF >> /infrabox/upload/archive/error_msg.log
health_check: git clone vflow repo failed!
EOF
  die "## git clone vflow repo failed!"
fi


if [ -d "vflow/e2e-test" ]; then
  VFLOW_TEST_FOLDER="e2e-test"
  REPORT_FILE_NAME_PREFIX="e2e_report_"
else
  VFLOW_TEST_FOLDER="integration-test"
  REPORT_FILE_NAME_PREFIX="integration_report_"
fi


echo '## Install the requirements and init connections'
pushd vflow/${VFLOW_TEST_FOLDER}
git log -20 --date-order > /infrabox/upload/archive/recent_commit.log
cp /infrabox/upload/archive/recent_commit.log ${LOG_OUTPUT_DIR}

RETRY_INSTANCE=5
if [ -n "${HDFS_CONNECTION_ID}" ];then
  declare -a api_arr=("app/datahub-app-connection")
  for api in "${api_arr[@]}"
  do
    echo "Try the api address ${api}"
    for((i=1;i<=${RETRY_INSTANCE};i++));
    do
        curl -vkL -X POST -H "X-Requested-With:Fetch" -H "Content-Type:application/json" -u "$VORA_TENANT\\${VORA_USERNAME}:${VORA_PASSWORD}" -d "{\"id\":\"${HDFS_CONNECTION_ID}\",\"licenseRelevant\":true,\"type\":\"HDFS\",\"contentData\":{\"host\":\"${HDFS_ENDPOINT}\",\"port\":${HDFS_PORT},\"protocol\":\"${HDFS_PROTOCOL}\",\"user\":\"${HDFS_USER}\"},\"changedNote\":\"\",\"tags\":[]}" ${VSYSTEM_ENDPOINT}/${api}/connections
        sleep 30 # sleep for the connection ready
        HDFS_CONNECTION_STATUS=$(curl -k --user "$VORA_TENANT\\${VORA_USERNAME}:${VORA_PASSWORD}" -H "X-Requested-With" ${VSYSTEM_ENDPOINT}/${api}/connections/${HDFS_CONNECTION_ID}/status)
        echo ${HDFS_CONNECTION_STATUS} | grep -i "status" | grep -i "OK"
        if [ $? == 0 ]; then
            echo "HDFS Connection Status OK!"
            break 2
        else
            echo "WARNING! Connection status check with ${api}/connections/${HDFS_CONNECTION_ID}/status failed. retry ..."
        fi
    done
  done
fi

# Create a unique username for each vflow job so they can run in parallel in different pods
create_unique_user() {
  RETRY=3
  for ((i = 1; i <= ${RETRY}; i++)); do
    vctl user create ${VORA_TENANT} ${VORA_USERNAME} ${VORA_PASSWORD} "tenantAdmin"
    vctl login ${VSYSTEM_ENDPOINT} ${VORA_TENANT} ${VORA_USERNAME} -p ${VORA_PASSWORD} --insecure
    CURRENT_USER=$(vctl whoami | awk -F '[ :]' '{print $4}')
    if [ $CURRENT_USER = $VORA_USERNAME ]; then
      break
    elif [ $i -eq ${RETRY} ]; then
      echo "### [level=error] The attempt to create a unique username has failed."
    else
      sleep 2
    fi
  done
}

version_ge(){
  test "$(echo "$@" | tr " " "\n" | sort -rV | head -n 1)" == "$1"; }

# Start a vFlow instance for the current user 
start_vflow() {
  RETRY=6
  for ((i = 1; i <= ${RETRY}; i++)); do
    if vctl scheduler start pipeline-modeler; then
      break
    elif [ $i -eq ${RETRY} ]; then
      cat << EOF >> /infrabox/upload/archive/error_msg.log
health_check:No VFLOW pod running!
EOF
      die "### [level=error] Could NOT start pipeline modeler for user ${VORA_USERNAME}"
    else
      sleep 10
    fi
  done
}

# Login using default user name first and then create a new user
vctl login ${VSYSTEM_ENDPOINT} ${VORA_TENANT} ${VORA_USERNAME} -p ${VORA_PASSWORD} --insecure
VORA_USERNAME="vflow-$(cat /proc/sys/kernel/random/uuid)"
create_unique_user

# DM01-2802 from vsolution 2210.6.0, no need to start pipeline-modeler
if [[ "${PROVISION_PLATFORM}" == "DHAAS-AWS" ]] && [[ -n "${VSOLUTION_VERSION}" ]]; then
    if version_ge "${VSOLUTION_VERSION}" "2210.6.0"; then
        echo "DM01-2802 from vsolution 2210.6.0, no need to start pipeline-modeler"
    else
        sleep 10 && start_vflow 
        # Find the pod where the tests are to be executed
        VFLOW_POD=$(kubectl get pods -l vora-component=vflow,vsystem.datahub.sap.com/user=${VORA_USERNAME},vsystem.datahub.sap.com/tenant=${VORA_TENANT} -n $NAMESPACE -o go-template --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' | head -1)
        if [ -z "${VFLOW_POD}" ]; then
            cat << EOF >> /infrabox/upload/archive/error_msg.log
health_check:No VFLOW pod running!
EOF
            die "## No vflow pod running !! Please check the datahub install job."
        fi
    fi
fi
VSYSTEM_OPTION=""
VFLOW_POD_OPTION="-p $VFLOW_POD"
if [[ -n "${ENABLE_VSYSTEM_OPTION}" ]] && [[ "${ENABLE_VSYSTEM_OPTION}" == "TRUE" ]]; then
  VSYSTEM_OPTION="--vsystem ${VSYSTEM_ENDPOINT}"
  VFLOW_POD_OPTION=""
fi

# remove the kubectl proxy process
kill -9 $(ps aux | grep kubectl | grep -v grep | awk '{print $2}') > /dev/null 2>&1

virtualenv -p python3 virtualenv
source virtualenv/bin/activate

echo '## Run vFlow tests'
SKIP_TESTS="$SKIP_TESTS advanced.vsolution_sandbox"
vit --ignore-solutions ${VSYSTEM_OPTION} --tenant ${VORA_TENANT} --user ${VORA_USERNAME} --password ${VORA_PASSWORD} ${VFLOW_POD_OPTION} --xml ${EXTERNAL_FLAG} --skip $SKIP_TESTS --retries $RETRY_TEST -n $NAMESPACE $SCENARIO_LIST 2>&1 | tee execution_logs.txt; job_status=${PIPESTATUS[0]}
deactivate

echo '## Finish execution'
# Upload the test result XML
echo ${LOG_OUTPUT_DIR} /infrabox/upload/archive /infrabox/upload/testresult | xargs -n 1 cp ${REPORT_FILE_NAME_PREFIX}*.xml
# dump the k8s
dump_k8s_cluster_info

# Copy diagnostic information from the failed graphs and execution logs
cp -r diagnostics /infrabox/upload/archive/diagnostics
cp execution_logs.txt /infrabox/upload/archive
popd

if [[ ${job_status} -ne 0 ]];then
  echo "run vflow_test failed! status code is ${job_status}"
  exit 1
fi

echo "## vFlow test done"

rm -rf vflow
