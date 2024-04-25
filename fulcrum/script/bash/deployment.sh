#!/bin/bash 

echo "## Start cluster auto deployment at: ${PROVISION_PLATFORM} ..."

export WORKSPACE=/ansible/
export OUTPUT_DIR=/infrabox/output/

if [[ -n ${VORA_COMMAND} ]];then
  echo "vora command is ${VORA_COMMAND}"
else
  echo "No command type specified , will take install as default..."
  export VORA_COMMAND="install"
fi

if [[ -n ${GIT_URL} ]];then
  git config --global http.sslVerify false
  mkdir /tmp/bdh-infra-tools
  if [[ -n ${GIT_BRANCH} ]];then
    git clone ${GIT_URL} -b ${GIT_BRANCH} /tmp/bdh-infra-tools
  else
    git clone ${GIT_URL} /tmp/bdh-infra-tools
  fi
  chmod +x /tmp/bdh-infra-tools
  pushd /tmp/bdh-infra-tools
  if [[ -n ${GIT_COMMIT} ]];then
    git checkout -qf ${GIT_COMMIT}
  fi
  git rev-parse --short HEAD

  if [[ -x ${WORKSPACE} ]];then
    mv ${WORKSPACE} /ansible.bak/
  fi
  mkdir /ansible
  chmod +x /ansible
  cp -r /tmp/bdh-infra-tools/common/ansible/* /ansible
  chmod 600 /ansible/id_rsa
  if [ -n ${MONSOON_HOSTS} ]; then
    cp /ansible.bak/${MONSOON_HOSTS} /ansible/inventories/monsoon_hosts
  fi
  popd
fi

if [ -f /ansible/${MONSOON_HOSTS} ]; then
  cp -f /ansible/${MONSOON_HOSTS} /ansible/inventories/monsoon_hosts
fi

if [[ -n ${USE_FOR} ]]; then
  if [[ ${PROVISION_PLATFORM} == "MONSOON" ]] || [[ ${PROVISION_PLATFORM} == "GKE" ]] || [[ ${PROVISION_PLATFORM} == "AZURE-AKS" ]] || [[ ${PROVISION_PLATFORM} == "AWS" ]] || [[ ${PROVISION_PLATFORM} == "AWS-EKS" ]] || [[ ${PROVISION_PLATFORM} == "GARDENER-AWS" ]] || [[ ${PROVISION_PLATFORM} == "GARDENER-CCLOUD" ]]; then
    /ansible/tools/infrabox-deploy-vora.sh ${PROVISION_PLATFORM}
  fi
elif [[ -n ${UNDEPLOYMENT} ]] && [[ ${UNDEPLOYMENT} == "true" ]];then
  /ansible/tools/jenkins-destroy-cluster.sh ${PROVISION_PLATFORM}
else
  if [[ ${PROVISION_PLATFORM} == "MONSOON" ]];then
    /ansible/tools/jenkins-deploy-k8s-vora.sh ${PROVISION_PLATFORM}
  elif [[ ${PROVISION_PLATFORM} == "GKE" ]] || [[ ${PROVISION_PLATFORM} == "AWS" ]] || [[ ${PROVISION_PLATFORM} == "AZURE-AKS" ]] || [[ ${PROVISION_PLATFORM} == "GARDENER-AWS" ]] || [[ ${PROVISION_PLATFORM} == "GARDENER-CCLOUD" ]];then
    /ansible/tools/jenkins-deploy-k8s-vora-cloud.sh ${PROVISION_PLATFORM}
  else
    echo "Not supported privision platform: ${PROVISION_PLATFORM}"
  fi
fi

