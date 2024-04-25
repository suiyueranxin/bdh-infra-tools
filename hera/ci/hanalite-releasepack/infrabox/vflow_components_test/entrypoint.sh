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
LOG_OUTPUT_DIR="/infrabox/output/execution_log/vflow"
mkdir -p $LOG_OUTPUT_DIR
GIT_SSL_NO_VERIFY=1
echo "## Start vflow testing..."

echo VORA_TENANT=$VORA_TENANT
echo VORA_USERNAME=$VORA_USERNAME
echo VORA_PASSWORD=$VORA_PASSWORD
echo NODE_HOST=$NODE_HOST
echo VSYSTEM_PORT=$VSYSTEM_PORT
echo NAMESPACE=$NAMESPACE

git config --global http.sslVerify false

download_vctl

kubectl version

# call this function in $COM_VFLOW_FOLDER
get_scenario_list_file() {
   SCENARIO_LIST_FILE="vflow_scenario_list.csv"
   if [[ ${PATH_TO_SCENARIO_FILE} ]]; then
       SCENARIO_LIST_FILE="${PATH_TO_SCENARIO_FILE}/${SCENARIO_LIST_FILE}"
   else
       # recursive search SCENARIO_LIST_FILE
       SCENARIO_LIST_FILE=$(find . -name ${SCENARIO_LIST_FILE} | head -1)
   fi
}

checkout_component() {
  repository=$1
  component_version=$2
  component_name=$(echo ${repository##*/} | awk -F  . '{print $1}')
  git clone $repository
  pushd $component_name
  if [ $component_version ]; then
    component_version_tag=$(git tag | grep $component_version | grep "rel")
    if [ $component_version_tag ]; then
      echo "${component_name} tag is ${component_version_tag}"
      git checkout -b e2e-push ${component_version_tag}
    fi
  fi
  popd
}

echo '## Clone vFlow'
git clone --single-branch --branch rel/$VFLOW_VERSION git@github.wdf.sap.corp:velocity/vflow.git
if [ $? != 0 ]; then
  cat << EOF >> /infrabox/upload/archive/error_msg.log
health_check: git clone vflow repo failed!
EOF
  die "## git clone vflow repo failed!"
fi

if [ -d "/vflow/e2e-test" ]; then
  VFLOW_TEST_FOLDER="e2e-test"
  REPORT_FILE_NAME_PREFIX="e2e_report_"
else
  VFLOW_TEST_FOLDER="integration-test"
  REPORT_FILE_NAME_PREFIX="integration_report_"
fi

if [ -n "${GIT_REPO}" ]; then
    if [[ ${COMPONENT_NAME} ]]; then
      checkout_component ${GIT_REPO} `eval echo '$'"$COMPONENT_NAME""_VERSION"`
    else
      git clone ${GIT_REPO}
      if [ $? != 0 ]; then
        cat << EOF >> /infrabox/upload/archive/error_msg.log
      health_check: git clone ${GIT_REPO} repo failed!
EOF
        die "## git clone ${GIT_REPO} repo failed!"
      fi
    fi
    COM_VFLOW_FOLDER=$(echo ${GIT_REPO##*/} | awk -F  . '{print $1}')
    pushd $COM_VFLOW_FOLDER
      git log -20 --date-order > /infrabox/upload/archive/recent_commit.log
      cp /infrabox/upload/archive/recent_commit.log ${LOG_OUTPUT_DIR}
      if [[ $VFLOW_COM_BRANCH ]] && [[ "$VFLOW_COM_BRANCH" != "master" ]]; then
          git checkout $VFLOW_COM_BRANCH
      fi
      if [ $VFLOW_COM_PATCHSET_REF ];then
          git fetch ${GIT_REPO} $VFLOW_COM_PATCHSET_REF && git checkout FETCH_HEAD
      fi 
      get_scenario_list_file
    popd

    if [ ! -s ${COM_VFLOW_FOLDER}/${SCENARIO_LIST_FILE} ]; then
        echo "${SCENARIO_LIST_FILE} is empty. Skip the test job"
        exit 1
    fi
    COM_VFLOW_FOR_ALL=$(cat ${COM_VFLOW_FOLDER}/${SCENARIO_LIST_FILE} |grep all |awk -F"," '{print $1}' |xargs)
    COM_VFLOW_FOR_NIGHTLY=$(cat ${COM_VFLOW_FOLDER}/${SCENARIO_LIST_FILE} |grep continuous-validation |awk -F"," '{print $1}' |xargs)
    COM_VFLOW_FOR_PUSH=$(cat ${COM_VFLOW_FOLDER}/${SCENARIO_LIST_FILE} |grep push-validation |awk -F"," '{print $1}' |xargs)
    # copy the test folders
    cat ${COM_VFLOW_FOLDER}/${SCENARIO_LIST_FILE}
    declare -a TEST_FOLDERS
    for line in $(cat ${COM_VFLOW_FOLDER}/${SCENARIO_LIST_FILE} | grep -v "#")
    do
      COM_SCENARIO_FOLDER=$(echo $line |awk -F"." '{print $1}')
      echo $COM_SCENARIO_FOLDER
      if [[ ! $(echo ${TEST_FOLDERS[@]}) =~ $COM_SCENARIO_FOLDER ]]; then
        TEST_FOLDERS=(${TEST_FOLDERS[@]} $COM_SCENARIO_FOLDER)
      fi
    done
    echo "Test folders are: ${TEST_FOLDERS[@]}"
    i=0
    for FOLDER in ${TEST_FOLDERS[@]}
    do
       cp -r $COM_VFLOW_FOLDER/$FOLDER /vflow/${VFLOW_TEST_FOLDER}/scenarios/
       let i++
    done
fi

echo '## Install the requirements and init connections'
pushd /vflow/${VFLOW_TEST_FOLDER}

# remove the kubectl proxy peocess
kill -9 `ps aux |grep kubectl |grep -v grep | awk '{print $2}'`  > /dev/null 2>&1
# Run graphs for nightly by default
SCENARIO_LIST="$COM_VFLOW_FOR_ALL $COM_VFLOW_FOR_NIGHTLY"
if [[ ${CONTINUES_INTEGRATION} = "FALSE" ]];then
    SCENARIO_LIST="$COM_VFLOW_FOR_ALL $COM_VFLOW_FOR_PUSH"
fi

if [[ $PROVISION_PLATFORM == "MONSOON" ]]; then
  EXTERNAL_FLAG=" "
else
  EXTERNAL_FLAG=" --external"
fi

SKIP_TESTS_OPTION=""
if [ -n "${SKIP_TESTS}" ]; then
  SKIP_TESTS_OPTION="--skip ${SKIP_TESTS}"
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

virtualenv -p python3 virtualenv
source virtualenv/bin/activate

echo '## Run vFlow tests'
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
  echo "run test failed! status code is ${job_status}"
  exit 1
fi

echo "## Vflow test done"

rm -rf /vflow

