#!/bin/bash
set -x
source ${ENV_FILE}
source /project/common.sh

echo "## Start content upgrade test"

echo "## Set DI_NAMESPACE env variable"
if [[ -z "${NAMESPACE}" ]]; then
  export DI_NAMESPACE=$(kubectl get ns | grep -v -e kube-public -e kube-system -e default -e datahub-system | awk 'FNR == 2 {print $1}')
else
  export DI_NAMESPACE=${NAMESPACE}
fi

echo "## Download vctl"

download_vctl

echo "## Content upgrade"
python vctl-start-app.py
job_status=$?

# dump the k8s
dump_k8s_cluster_info

if [[ ${job_status} -ne 0 ]]; then
  echo "run content_upgrade_test failed!"
  exit 1
fi
