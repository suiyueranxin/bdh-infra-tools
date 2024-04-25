#!/bin/bash

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

echo "## start voratools test..."

download_vctl
if ! vctl --help >/dev/null 2>&1; then
  VCTL_CHECK=1
else
  VCTL_CHECK=0
  echo "##Create voratools instance"
  vctl login ${VSYSTEM_ENDPOINT} ${VORA_TENANT} ${VORA_USERNAME} -p ${VORA_PASSWORD} --insecure
  VORA_USERNAME="tmpuser-$(cat /proc/sys/kernel/random/uuid)"
  create_unique_user && sleep 10
  RETRY=3
  for ((i = 1; i <= ${RETRY}; i++)); do
    vctl login ${VSYSTEM_ENDPOINT} ${VORA_TENANT} ${VORA_USERNAME} -p ${VORA_PASSWORD} --insecure
    vctl scheduler start vora-tools
    sleep 30s # wait pods up
    VORATOOLS_POD=$(kubectl get pods -l datahub.sap.com/app=vsystem,datahub.sap.com/app-component=vsystem-app,vsystem.datahub.sap.com/user=${VORA_USERNAME},vsystem.datahub.sap.com/tenant=${VORA_TENANT} -n ${NAMESPACE} -o go-template --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' | grep vora-tools)
    if [ -z "${VORATOOLS_POD}" ]; then
      if [[ $i < ${RETRY} ]]; then
        echo "create instance failed. Retry..."
        sleep 1m
        continue
      fi
      CREATE_INSTANCE=1
    else
      CREATE_INSTANCE=0
      break
    fi
  done
fi

if [[ $VCTL_CHECK != 0 || $CREATE_INSTANCE != 0 ]];then
  RESULT=1
else
  RESULT=0
fi

python ./project/check_voratools_status.py $RESULT

if [[ $VCTL_CHECK != 0 ]];then
  die "## Warning! No vctl binary found! Cannot create voratools instance!"
fi

if [[ $CREATE_INSTANCE != 0 ]];then
  echo "## Create voratools instance failed!"
  exit 0
fi

echo "voratools test done..."

