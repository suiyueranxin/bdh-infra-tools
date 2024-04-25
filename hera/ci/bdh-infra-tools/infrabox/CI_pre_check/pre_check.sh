#!/bin/bash

set -x

# Get the BDH info from env.sh
if [ -n "${PARENT_INSTALL_JOB}" ]; then
  ENV_FILE="/infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh"
  if [ ! -f ${ENV_FILE} ]; then
    echo "${ENV_FILE} does not exist. Skip the current job"
    exit 1
  else
    source ${ENV_FILE}
  fi
else
  echo "## No env.sh, health check can't start!"
  exit 1
fi

echo "## health check starts."

if [ -f "$KUBECONFIG" ]; then
 # judge if kubectl is exist
  python -c"import kubernetes"
  if [ $? -ne 0 ]; then
    echo "python kubernetes client was not installed, will skip cluster check"
    export SKIP_CLUSTER_CHECK="yes"
  fi
  if [[ $PROVISION_PLATFORM ]] && [[ $PROVISION_PLATFORM == MONSOON ]]; then
    unset no_proxy
    unset http_proxy
    unset https_proxy
  fi
fi
python /project/bdh_health_check.py
HEALTH_CHECK_RESULT=$?

if [[ $HEALTH_CHECK_RESULT != 0 ]] ; then
    echo "ERROR: CI pre check fails!"
    exit 1
fi
echo "## CI pre check is done. Job will start!"
