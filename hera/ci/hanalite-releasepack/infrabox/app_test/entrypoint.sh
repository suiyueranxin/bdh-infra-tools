#!/bin/bash

SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

if [ -n "${PARENT_INSTALL_JOB}" ]; then
  if [ ! -f /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh ]; then
    echo "/infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh does not exist."
    if [ ! -f /infrabox/inputs/${PARENT_INSTALL_JOB}/bdh_base_version.sh ]; then
      echo "/infrabox/inputs/${PARENT_INSTALL_JOB}/bdh_base_version.sh does not exist. Skip the current job"
      exit 0
    else
      echo "/infrabox/inputs/${PARENT_INSTALL_JOB}/bdh_base_version.sh exists. Use env variables from the base version"
      source /infrabox/inputs/${PARENT_INSTALL_JOB}/bdh_base_version.sh
      echo "Set KUBECONFIG to /infrabox/inputs/${PARENT_INSTALL_JOB}/admin.conf"
      export KUBECONFIG=/infrabox/inputs/${PARENT_INSTALL_JOB}/admin.conf
    fi
  else
    echo "Set KUBECONFIG to /infrabox/inputs/${PARENT_INSTALL_JOB}/admin.conf"
    export KUBECONFIG=/infrabox/inputs/${PARENT_INSTALL_JOB}/admin.conf
    source /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh
  fi

  if [[ ${UPGRADE_TEST} && -f /infrabox/inputs/fetch-e2e-secrets/e2e_secrets.env ]]; then 
    echo "/infrabox/inputs/fetch-e2e-secrets/e2e_secrets.env exists."
    source /infrabox/inputs/fetch-e2e-secrets/e2e_secrets.env
  fi

else
  echo "## Skip sourcing env.sh, Using external env information..."
fi

if [[ ${UPGRADE_TEST} && ${BASE_BDH_VERSION:0:3} == "2.4" ]]; then
    echo "## Skip content validation in case of an upgrade from 2.4"
else 
  source ${SCRIPTPATH}/prepare_app_test.sh
  source ${SCRIPTPATH}/run_test.sh
fi
