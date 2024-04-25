#!/bin/bash
set -ex

if [ -n "${PARENT_INSTALL_JOB}" ]; then
  ENV_FILE="/infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh"
  if [ ! -f ${ENV_FILE} ]; then
    echo "${ENV_FILE} does not exist."
    exit 1
  else
    source ${ENV_FILE}
  fi
else
  echo "### [level=warning] env PARENT_INSTALL_JOB was not defined."
  exit 1
fi
source /project/common.sh

# cut the -SNAPSHOT suffix eg: 2.6.51-SNAPSHOT -> 2.6.51
if [[ ${VSYSTEM_VERSION} == *-SNAPSHOT* ]]
then
    VSYSTEM_SNAPSHOT=${VSYSTEM_VERSION}
    echo "Over write $VSYSTEM_VERSION by ${VSYSTEM_VERSION%-SNAPSHOT*}"
    export VSYSTEM_VERSION=${VSYSTEM_VERSION%-SNAPSHOT*}
    sed -i "/VSYSTEM_VERSION/s/${VSYSTEM_SNAPSHOT}/${VSYSTEM_VERSION}/g" ${ENV_FILE}
fi

# set vctl bin path
if [ ! -f /infrabox/inputs/${PARENT_INSTALL_JOB}/vctl ]; then
  # DHAAS or other situation
  set +e
  download_vctl
  cp ./vctl /infrabox/inputs/${PARENT_INSTALL_JOB}/vctl
  set -e
fi
export VCTL_BIN="/infrabox/inputs/${PARENT_INSTALL_JOB}/vctl"
cp ${VCTL_BIN} /usr/local/bin/
python /project/entrypoint.py
