#!/bin/bash

################################################################################
# Starting docker service takes few seconds so we need to wait until it is done
# It is a must have for minikube with vm-driver=none. Otherwise there are no
# nodes available for k8s minikube cluster: "no nodes available to schedule pods"
################################################################################

echo "## Starting docker daemon"

mkdir -p /etc/docker

if [[ -n ${DEV_CONFIG_FILE_CONTENT} ]]; then
  TMP_DEV_CONFIG_FILE=/tmp/tmp_dev_config
  echo "${DEV_CONFIG_FILE_CONTENT}" >> ${TMP_DEV_CONFIG_FILE}
  sed -i 's/\\n/\n/g' ${TMP_DEV_CONFIG_FILE}
  sudo python /ansible/tools/update_docker_daemon.py ${TMP_DEV_CONFIG_FILE}
fi

if [[ -n ${DEV_CONFIG_FILE} ]] && [[ -f "/ansible/tools/update_docker_daemon.py" ]]; then
  sudo python /ansible/tools/update_docker_daemon.py ${DEV_CONFIG_FILE}
fi

if [ -f /etc/docker/daemon.json ]; then
  echo "## /etc/docker/daemon.json content:"
  cat /etc/docker/daemon.json
fi

service docker start
