#!/bin/bash

set -x

if [ -n "${PARENT_INSTALL_JOB}" ]; then
  if [ ! -f /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh ]; then
    echo "/infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh does not exist."
    exit 1
  else
    source /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh
  fi
else
  echo "### [level=warning] Skip sourcing env.sh, Using external env information..."
fi

if [[ -n ${DEV_CONFIG_FILE_CONTENT} ]]; then
  echo "## reading dev config"
  DEV_CONFIG_FILE=/project/tmp_dev_config
  mkdir -p /project
  echo "${DEV_CONFIG_FILE_CONTENT}" > ${DEV_CONFIG_FILE}
  sed -i 's/\\n/\n/g' ${DEV_CONFIG_FILE}
fi

if [[ -n ${DEV_CONFIG_FILE} ]]; then
  cat ${DEV_CONFIG_FILE}
  source ${DEV_CONFIG_FILE}
fi

# wait for docker service running
RETRY=6
for ((loop = 1; loop <= ${RETRY}; loop++)); do
  service docker status | grep "Docker is running"
  if [ $? -ne 0 ]; then
     if [[ ${loop} < ${RETRY} ]]; then
       echo "docker deamon is not ready. retry..."
       service docker start
       sleep 10
       continue
     fi
     echo "## Warning! Docker daemon is not running! Exit the job!"
     exit 1
  else
     echo "docker daemon is running."
     break
  fi
done

echo "## service vora-tx-coordinator-ext"
kubectl get services -n $NAMESPACE

kubectl describe service vora-tx-coordinator-ext -n $NAMESPACE

if [[ -n ${VORA_DQP_TEST_IMAGE_SOURCE_CUSTOM} ]] && [[ -n ${VORA_DQP_TEST_IMAGE_TAG_CUSTOM} ]]; then
  IMAGE=${VORA_DQP_TEST_IMAGE_SOURCE_CUSTOM}/com.sap.datahub.linuxx86_64/vora-dqp-test-framework:${VORA_DQP_TEST_IMAGE_TAG_CUSTOM}
  echo "## pulling custom ${IMAGE}"
  docker pull ${IMAGE}
  ret=$?
else
  REPO="docker.wdf.sap.corp:51022"
  IMAGE="${REPO}/com.sap.datahub.linuxx86_64/vora-dqp-test-framework:${HANALITE_LIB_VERSION}"
  echo "## pulling default ${IMAGE}"
  docker pull ${IMAGE}
  ret=$?
  if [ $ret -ne 0 ]; then
    echo "### [level=warning] pulling ${IMAGE} failed"
    REPO="docker.wdf.sap.corp:51055"
    IMAGE="${REPO}/com.sap.datahub.linuxx86_64/vora-dqp-test-framework:${HANALITE_LIB_VERSION}"
    echo "## pulling fallback ${IMAGE}"
    docker pull ${IMAGE}
    ret=$?
  fi
fi

# extend the container env.
RUNTIME_ENV_FILE="runtime.env"

# workaround TODO use python to filter the env
unset GERRIT_CHANGE_COMMIT_MESSAGE
unset DEV_CONFIG_FILE_CONTENT
env | grep -vw 'no_proxy\|HOSTNAME\|HOME\|https_proxy\|http_proxy\|TERM\|PATH\|PWD\|LS_COLORS\|SHLVL\|LESSOPEN\|LESSCLOSE\|_' | awk  -F '=' '{print $1}' > ${RUNTIME_ENV_FILE}
RUNTIME_ENV_FILE_OPTION="--env-file ${RUNTIME_ENV_FILE}"
cat $RUNTIME_ENV_FILE

echo "## executing test image ${IMAGE}"
docker run -v /infrabox:/infrabox ${RUNTIME_ENV_FILE_OPTION} "${IMAGE}"
job_status=$?
if [[ "${ENABLE_DEPLOYMENTS}" == "yes" ]] && [[ ${JOB_NAME} ]]; then
  REGISTRY="di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools"
  docker tag "${IMAGE}" ${REGISTRY}/troubleshooting/${JOB_NAME}:build_${INFRABOX_BUILD_NUMBER}
  docker push ${REGISTRY}/troubleshooting/${JOB_NAME}:build_${INFRABOX_BUILD_NUMBER}
fi
if [[ ${job_status} -ne 0 ]];then
  echo "run hanalite_dqp_test failed! status code is ${job_status}"
  exit 1
fi
echo "run hanalite_dqp_test complete!"
