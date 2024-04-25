#!/bin/bash
set -x

USAGE="$0 MONSOON"
ANSIBLE_ROOT_DIR="/ansible"
LOG_OUTPUT_DIR="/infrabox/output/execution_log"
mkdir -p $LOG_OUTPUT_DIR
if [ -n "${K8S_CREATION_JOB}" ]; then
  export KUBECONFIG="/infrabox/inputs/${K8S_CREATION_JOB}/admin.conf"
  if [ ! -f $KUBECONFIG ]; then
    echo "$KUBECONFIG does not exist. Skip the current job"
    exit 0
  else
    echo $KUBECONFIG exist
  fi
else
  echo "## Skip KUBECONFIG env setting, Using external env information..."
fi

# para: "uninstall" or "installation"
copy_log() {
  if [[ "${INSTALL_VIA_SLCB}" == "true" ]] || [[ "${UNINSTALL_VIA_SLCB}" == "true" ]]; then
    cp ${ANSIBLE_ROOT_DIR}/playbooks/vora/slcb*.log /infrabox/upload/archive
    if [ -f ${ANSIBLE_ROOT_DIR}/playbooks/vora/inifile ]; then
      cp ${ANSIBLE_ROOT_DIR}/playbooks/vora/inifile /infrabox/upload/archive
    fi
  else
    echo ${LOG_OUTPUT_DIR}/vora_$1.log /infrabox/upload/archive/vora_$1.log | xargs -n 1 cp ${ANSIBLE_ROOT_DIR}/playbooks/vora/vora_$1.log   
  fi
  cp ${ANSIBLE_ROOT_DIR}/playbooks/vora/*.zip ${LOG_OUTPUT_DIR}
  cp ${ANSIBLE_ROOT_DIR}/playbooks/vora/*.zip /infrabox/upload/archive
  cp ${ANSIBLE_ROOT_DIR}/playbooks/vora/*.tgz /infrabox/output/
  cp ${ANSIBLE_ROOT_DIR}/playbooks/vora/*.tgz /infrabox/upload/archive
}

# get vctl from installer job
get_vctl_from_installer() {
  TOOLS="/infrabox/output/tools.tgz"
  if [[ ! -f ${TOOLS} ]]; then
    echo "No tools.tgz found"
    return 1
  fi
  if [[ -f ${TOOLS} ]]; then
    tar -zxf ${TOOLS} -C /
    if [ ! -f "/tools/vctl" ];then
      echo "Extract vctl package failed!"
    fi
    chmod +x /tools/vctl
    cp /tools/vctl ./; cp /tools/vctl /usr/local/bin/
    cp /tools/vctl /infrabox/output/
  fi
  return 0
}

create_calico_netpol_logger() {
#  set -e
  pushd /tmp
  git config --global http.sslVerify false
  git clone git@github.wdf.sap.corp:I354116/calico-netpol-logger.git
  export DATASTORE_TYPE=kubernetes
  pushd calico-netpol-logger
  calicoctl apply -f calico_logging_rule.yaml --namespace $NAMESPACE
  ./setup.sh
  popd
  popd
#  set +e
}

get_installer_pkg_file() {
  INFRABOX_INPUT_BUILD=$(dirname "$VORA_ENV_FILE")
  ls -alh $INFRABOX_INPUT_BUILD
  PACKAGE_PATTERN="Foundation"
  if [[ -n "${VORA_KUBE_SUFFIX}" ]]; then
    PACKAGE_PATTERN=${VORA_KUBE_SUFFIX}
  fi
  find /infrabox/inputs -mindepth 2 -maxdepth 2 -name \*${PACKAGE_PATTERN}.tar.gz
  export VORA_PACKAGE=$(find /infrabox/inputs -mindepth 2 -maxdepth 2 -name \*${PACKAGE_PATTERN}.tar.gz)
  if ! [ -f "$VORA_PACKAGE" ]; then
    echo "could not find ${PACKAGE_PATTERN}.tar.gz from /infrabox/inputs"
    exit 1
  fi
}

mirror_bridge_images() {
  IMAGE_LIST=$(find /infrabox/inputs -mindepth 2 -maxdepth 2 -name "slcb_image_list.txt")
  # always use skopeo to mirror images
  source ${ROOT_DIR}/tools/pull_and_push_docker_image.sh
  mirror_image ${IMAGE_LIST}
}

update_env() {
  pushd ${ROOT_DIR}
    repo="ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack"
    clone_repo $repo
    if [ $? -ne 0 ]; then
      echo "clone ${repo} failed"
      exit 1
    fi
    pushd ${ROOT_DIR}/hanalite-releasepack
      get_tag_by_version_and_branch ${VORA_VERSION} ${GERRIT_CHANGE_BRANCH}
      if [ $VORA_VERSION_TAG ]; then
        git checkout -b e2e-push $VORA_VERSION_TAG
        echo "## VORA_VERSION_TAG: ${VORA_VERSION_TAG}"
      fi
      if [ -z "${ALL_COMPONENTS_VERSIONS}" ]; then
        cp ${ROOT_DIR}/tools/list_component_versions.py .
        cp ${ROOT_DIR}/tools/get_component_version.py .
        chmod +x list_component_versions.py
        chmod +x get_component_version.py
        get_component_version_from_pom
      fi
      # copy import.sh & export.sh out for import_export_test job
      cp src/main/kubernetes/tools/*.sh /infrabox/output/

      if [[ -z "${SLCB_VERSION}" ]]; then
        install_file="images/com.sap.datahub.linuxx86_64/installer/Dockerfile"
        LATEST_SLCB_VERSION=$(grep -E 'ARG SLC_BRIDGE_BASE_VERSION' ${install_file} |tr -d '[ARG SLC_BRIDGE_BASE_VERSION=]')
        export SLCB_VERSION=${LATEST_SLCB_VERSION}
      fi
    popd
  popd
}

remove_vora_cluster_from_deployments() {
  index=$(kubectl -n "${NAMESPACE}" get datahub default -o json | jq '.spec.deployments' | jq 'index("vora-cluster")')
  if [[ -n $index ]]; then
    kubectl -n "${NAMESPACE}" patch datahub default --type='json' -p="[{'op': 'remove', 'path': '/spec/deployments/$index'}]"
    echo "vora removed"
  else
    echo "no vora found when try to remove vora"
  fi
}

if [ $# -ne 1 ];then
   echo ${USAGE}
   exit 1
fi

if [[ -f "/infrabox/inputs/${K8S_CREATION_JOB}/k8s_namespace.txt" ]]; then
  export K8S_INSTALLER_NAMESPACE=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_namespace.txt)
else
  if [[ -z "${VORA_NAMESPACE_PREFIX}" ]]; then
    export K8S_INSTALLER_NAMESPACE="vora-${INFRABOX_BUILD_NUMBER}-${INFRABOX_BUILD_RESTART_COUNTER}"
  else
    export K8S_INSTALLER_NAMESPACE="${VORA_NAMESPACE_PREFIX}-${INFRABOX_BUILD_NUMBER}-${INFRABOX_BUILD_RESTART_COUNTER}"
  fi
fi
export NAMESPACE=${K8S_INSTALLER_NAMESPACE}

ftp_download() {
  if [[ "$FTPENABLE" == "TRUE" ]]; then
      /infrabox/context/hera/common/ftp_download.sh ${FTPHOST} ${FTPUSER} ${FTPPASS} ${K8S_INSTALLER_NAMESPACE} "/infrabox/inputs/build"
  fi
}

ftp_delete() {
  if [[ "$FTPENABLE" == "TRUE" ]]; then
    /infrabox/context/hera/common/ftp_delete.sh ${FTPHOST} ${FTPUSER} ${FTPPASS} ${K8S_INSTALLER_NAMESPACE}
  fi
}

export ROOT_DIR=$(dirname ${BASH_SOURCE[0]})/../

if [ -n "${INSTALL_LATEST_MILESTONE}" ] && [ "${INSTALL_LATEST_MILESTONE}" == "true" ];then
  cp ${ROOT_DIR}/tools/get_latest_milestone.py .
  chmod +x get_latest_milestone.py
  if [[ $GERRIT_CHANGE_BRANCH ]]; then
    VORA_VERSION=$(python get_latest_milestone.py ${GERRIT_CHANGE_BRANCH})
  else
    VORA_VERSION=$(python get_latest_milestone.py master)
  fi
fi

cp ${ROOT_DIR}/tools/get_password.py .
chmod +x get_password.py
VORA_PASSWORD=$(python get_password.py)
VORA_SYSTEM_TENANT_PASSWORD=$(python get_password.py)

source /infrabox/context/hera/common/common.sh

if [[ -n "${UNINSTALL_VIA_SLCB}" ]]; then
  export VORA_ENV_FILE=$(find /infrabox/inputs -mindepth 2 -maxdepth 2 -name env.sh | grep 'install')
  source "$VORA_ENV_FILE"
fi

if [[ -z "${VORA_VERSION}" ]]; then
  export VORA_ENV_FILE=$(find /infrabox/inputs -mindepth 2 -maxdepth 2 -name env.sh | grep 'build')
  if ! [ -f "$VORA_ENV_FILE" ]; then
    echo "could not find env.sh in any folder in /infrabox/inputs"
    find / > /infrabox/upload/archive/ls_root 2>&1 /dev/null
    exit 1
  fi

  source "$VORA_ENV_FILE"
  ftp_download
  

  if [[ -n "${INSTALL_VIA_SLCB}" ]] && [[ "${INSTALL_VIA_SLCB}" == "true" ]]; then
    # install with the SLC Bridge
    # mirror the images to jfrog as source
    echo "mirror Bridge images..."
    add_wdf_cer
    mirror_bridge_images
    export BRIDGE_BUILD_VERSION="build_${INFRABOX_BUILD_NUMBER}"
  else
    # install with the installer.sh
    # set the installer pkg file path to VORA_PACKAGE env.
    get_installer_pkg_file
  fi
fi
echo "vora version is: $VORA_VERSION"
set +e

#source common function for parser jenkins parameters
source ${ROOT_DIR}/tools/jenkins-cluster-utils.sh
env_file="/infrabox/output/env.sh"
#set this when deploy cluster without docker
ENABLE_VORA_INSTALLATION=${ENABLE_VORA_INSTALLATION:-"false"}
if [[ -n "${VORA_COMMAND}" ]];then
  echo "vora command is ${VORA_COMMAND}"
else
  VORA_COMMAND="install"
fi

if [[ -n "${DEV_CONFIG_FILE_CONTENT}" ]]; then
  DEV_CONFIG_FILE=${ROOT_DIR}/dev_config
  echo "${DEV_CONFIG_FILE_CONTENT}" >> ${DEV_CONFIG_FILE}
  sed -i 's/\\n/\n/g' ${DEV_CONFIG_FILE}
fi

if [[ -z "${DEV_CONFIG_FILE}" ]]; then
  DEV_CONFIG_FILE=$(find /infrabox/inputs -mindepth 2 -maxdepth 2 -name installation_config.sh)
fi
if [ ! -z "$DEV_CONFIG_FILE" ]; then
  echo "will use DEV_CONFIG_FILE=$DEV_CONFIG_FILE"
  cp $DEV_CONFIG_FILE /infrabox/output/dev_config.sh
fi

if [[ -n $BACKUP_JOB ]]; then
  input_env_file="/infrabox/inputs/${BACKUP_JOB}/env.sh"
  if [[ ! -f $input_env_file ]]; then
    echo "input_env_file does not exist. Skip the current job"
    exit 0
  else
    DI_BACKUP_NAME=$(cat ${input_env_file} | grep "DI_BACKUP_NAME" | awk -F '=' '{ print $2 }')
    echo "DI_BACKUP_NAME = ${DI_BACKUP_NAME}"
    VORA_PASSWORD=$(cat ${input_env_file} | grep "VORA_PASSWORD" | awk -F '=' '{ print $2 }')
    echo "VORA_PASSWORD = ${VORA_PASSWORD}"
    VORA_SYSTEM_TENANT_PASSWORD=$(cat ${input_env_file} | grep "VORA_SYSTEM_TENANT_PASSWORD" | awk -F '=' '{ print $2 }')
    echo "VORA_SYSTEM_TENANT_PASSWORD = ${VORA_SYSTEM_TENANT_PASSWORD}"
  fi
fi

export K8S_CLUSTER_NAME=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt)
export AUTH_HEADER=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/auth_header.txt)
CREDENTIAL_RETRY=3
for ((i = 1; i <= ${CREDENTIAL_RETRY}; i++))
do
  python ${ROOT_DIR}/tools/get_cloud_credentials.py ${K8S_CLUSTER_NAME} ${1} "/" "${AUTH_HEADER}"
  CREDENTIAL_RESULT=$?
  if [ ${CREDENTIAL_RESULT} -eq 0 ]; then
    echo "## Get GKE credential.json done."
    break
  fi
  if [ $i -lt ${CREDENTIAL_RETRY} ]; then
    sleep 10s
    continue
  else
    echo "## Failed to get gke credentials."
    exit 1
  fi
done

if [ ${1} != "GARDENER-CCLOUD" ]; then
  if [ ! -f '/credential.json' ]; then
    echo "## Failed to generate /credential.json."
    exit 1
  else
    cp /credential.json /infrabox/output/credential.json
  fi
fi

echo "Get vault value with IM API"
vault_item="system-access/jfrog/t_user_di_infra_cicd"
python /infrabox/context/common/ansible/tools/get_vault_value_with_im_api.py ${vault_item} "/" "${AUTH_HEADER}"

if [[ "${USE_FOR}" == "PUSH_VALIDATION" ]] || [[ "${USE_FOR}" == "NIGHTLY_VALIDATION_debug" ]] || [[ "${USE_CUSTOMIZED_SLCB_BINARY}" == "true" ]]; then
  DOCKER_ARTIFACTORY="di-dev-cicd-v2.int.repositories.cloud.sap/infrabox/hanalite-releasepack"
fi

#set different inventory file for different provisioning type
if [ ${1} == "MONSOON" ];then
  #copy hosts file into inventory directory
  hosts_file=${ROOT_DIR}/inventories/monsoon_hosts
  rm ${hosts_file}
  cp /infrabox/inputs/${K8S_CREATION_JOB}/hosts ${hosts_file}
  admin_conf=$KUBECONFIG
  HANA_RESOURCES_REQUESTS_MEMORY="6Gi"
  HANA_RESOURCES_LIMITS_MEMORY="15Gi"
  if [[ -n "${EXPOSE_PORT}" ]] && [[ ${EXPOSE_PORT} == "yes" ]]; then
    EXPOSE_VSYSTEM="yes"
    EXPOSE_VORA_TXC="yes"
    EXPOSE_TEXT_ANALYSIS="yes"
  fi
  ENABLE_NETWORK_POLICIES="yes"
  ENABLE_KANIKO="no"
  unset http_proxy
  unset https_proxy
  unset no_proxy
elif [ ${1} == "GKE" ]; then
  DEPLOY_DOCKER_CLUSTER="false"
  ENABLE_AUTHENTICATION="no"
  hosts_file="${ROOT_DIR}/inventories/hosts"
  admin_conf=$KUBECONFIG
  GKE_K8S_CLUSTER_KUBECONFIG="${admin_conf}"
  KUBE_ADMIN_CONFIG_PATH="${admin_conf}"
  CLOUD_PLATFORM="gke"
  GKE_K8S_CLUSTER_NAME="${K8S_CLUSTER_NAME}"
  GKE_BUCKET_NAME="${K8S_CLUSTER_NAME}"
  GCP_APPLICATION_CREDENTIALS="/credential.json"
  GKE_EXPOSE_INGRESS_AT_ROUTE53="yes"
  HANA_RESOURCES_REQUESTS_MEMORY="6Gi"
  HANA_RESOURCES_LIMITS_MEMORY="15Gi"
  if [[ "${VORA_COMMAND}" == "install" ]]; then
    if [[ "${INSTALL_VIA_SLCB}" == "true" ]] || [[ "${USE_SKOPEO}" == "yes" ]] || [[ "${UNINSTALL_VIA_SLCB}" == "true" ]]; then
      if [[ "${USE_CUSTOMIZED_SLCB_BINARY}" == "true" ]]; then
        export GCP_DOCKER_REGISTRY_SUFFIX=${K8S_CLUSTER_NAME}
      else 
        export GCP_DOCKER_REGISTRY_SUFFIX="validation-shared"
      fi
      export GCP_VFLOW_DOCKER_REGISTRY_SUFFIX=${K8S_CLUSTER_NAME} 
    else
      GCP_DOCKER_REGISTRY_SUFFIX=${K8S_CLUSTER_NAME}
    fi       
  else
    GCP_DOCKER_REGISTRY_SUFFIX=${K8S_CLUSTER_NAME}
  fi
  if [[ "${INSTALLER_VALIDATION}" == "yes" ]]; then
    ENABLE_NETWORK_POLICIES = ${ENABLE_NETWORK_POLICIES}
  else
    ENABLE_NETWORK_POLICIES="yes"
  fi
  ENABLE_KANIKO="yes"
  if [[ "${USE_FOR}" == "PUSH_VALIDATION" ]]; then
    #BDH_ONE_NODE_INSTALLATION="yes"
    HANA_RESOURCES_LIMITS_MEMORY="10Gi"
  fi
  if [[ -n "${EXPOSE_PORT}" ]] && [[ ${EXPOSE_PORT} == "yes" ]]; then
    EXPOSE_VSYSTEM="yes"
    EXPOSE_VORA_TXC="yes"
    EXPOSE_TEXT_ANALYSIS="yes"
  fi
elif [ ${1} == "AZURE-AKS" ]; then
  DEPLOY_DOCKER_CLUSTER="false"
  ENABLE_AUTHENTICATION="no"
  hosts_file="${ROOT_DIR}/inventories/hosts"
  admin_conf="/infrabox/inputs/${K8S_CREATION_JOB}/admin.conf"
  KUBE_ADMIN_CONFIG_PATH="${admin_conf}"
  AZURE_KUBECONFIG="${admin_conf}"
  CLOUD_PLATFORM="azure-aks"
  AZURE_RESOURCE_LOCATION=westeurope
  if [[ "${INSTALLER_VALIDATION}" == "yes" ]]; then
    ENABLE_NETWORK_POLICIES = ${ENABLE_NETWORK_POLICIES}
  else
    ENABLE_NETWORK_POLICIES="yes"
  fi
  ENABLE_KANIKO="yes"
  AKS_SECURITY_JSON_FILE="/credential.json"
  AKS_CLUSTER_NAME="${K8S_CLUSTER_NAME}"
  source /infrabox/inputs/${K8S_CREATION_JOB}/k8s_info.sh
  if [ -n "${K8S_CREATION_JOB}" ] && [[ -f /infrabox/inputs/${K8S_CREATION_JOB}/azure_cert_file.sh ]]; then
    source /infrabox/inputs/${K8S_CREATION_JOB}/azure_cert_file.sh
  fi 
  if [[ -z "${AKS_SUBSCRIPTION_NAME}" ]]; then
    AKS_FAST_DEPLOY="yes"
  else
    AKS_FAST_DEPLOY="yes"
      # on new azure installation: create dedicated registry for vflow;
      # use shared registry for installation
    #AZURE_VFLOW_REGISTRY_NAME=${AZURE_REGISTRY_NAME}
    if [[ "${AKS_SUBSCRIPTION_NAME}" == "PI Big Data Vora (SE)" ]]; then
      AZURE_VFLOW_REGISTRY_NAME = "infrabase"
      AZURE_REGISTRY_NAME = "infrabase"
    else
      # AZURE_VFLOW_REGISTRY_NAME = "dhvalregistry"
      # AZURE_REGISTRY_NAME = "dhvalregistry"
      AZURE_VFLOW_REGISTRY_NAME = ${AZURE_DOCKER_LOGIN_ADDRESS}
      AZURE_REGISTRY_NAME = ${AZURE_DOCKER_LOGIN_ADDRESS}
    fi
    AZURE_VFLOW_RESOURCE_GROUP=${AZURE_RESOURCE_GROUP}
    AZURE_RESOURCE_GROUP="bdh-infra"
  fi
elif [ ${1} == "AWS" ]; then
  DEPLOY_DOCKER_CLUSTER="false"
  ENABLE_AUTHENTICATION="no"
  hosts_file="${ROOT_DIR}/inventories/hosts"
  admin_conf="/infrabox/inputs/${K8S_CREATION_JOB}/admin.conf"
  KOPS_K8S_CLUSTER_KUBECONFIG="${admin_conf}"
  KUBE_ADMIN_CONFIG_PATH="${admin_conf}"
  CLOUD_PLATFORM="kops"
  AWS_SECURITY_JSON_FILE="/credential.json"
  KOPS_K8S_CLUSTER_NAME=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_bucket.txt) # workaround
  if [[ -z "${KOPS_K8S_CLUSTER_NAME}" ]]; then
    KOPS_K8S_CLUSTER_NAME="${K8S_CLUSTER_NAME}"
  fi
  if [[ -n "${EXPOSE_PORT}" ]] && [[ ${EXPOSE_PORT} == "yes" ]]; then
    EXPOSE_VSYSTEM="yes"
    EXPOSE_VORA_TXC="yes"
    EXPOSE_TEXT_ANALYSIS="yes"
  fi
elif [ ${1} == "AWS-EKS" ]; then
  DEPLOY_DOCKER_CLUSTER="false"
  ENABLE_AUTHENTICATION="no"
  #copy hosts file into inventory directory
  hosts_file="${ROOT_DIR}/inventories/hosts"
  rm ${hosts_file}
  cp /infrabox/inputs/${K8S_CREATION_JOB}/hosts ${hosts_file}
  admin_conf="/infrabox/inputs/${K8S_CREATION_JOB}/admin.conf"
  EKS_K8S_CLUSTER_KUBECONFIG="${admin_conf}"
  KUBE_ADMIN_CONFIG_PATH="${admin_conf}"
  CLOUD_PLATFORM="eks"
  AWS_SECURITY_JSON_FILE="/credential.json"
  EKS_K8S_CLUSTER_NAME=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_bucket.txt) # workaround
  if [ -n "$ENABLE_BACKUP" ]; then
    EKS_AWS_REGION="eu-central-1"
    EKS_AWS_S3_BUCKET_NAME="data-hub-im-kms2"
  else
    EKS_AWS_REGION="eu-west-1"
  fi
  # if [[ -n "${INSTALL_VIA_SLCB}" ]] && [[ ${INSTALL_VIA_SLCB} == "true" ]]; then
  #   ENABLE_NETWORK_POLICIES="no"
  # else
  #   INSTALL_VORA_VIA_SLPLUGIN="true"
  #   ENABLE_NETWORK_POLICIES="yes"
  # fi
  if [[ "${INSTALLER_VALIDATION}" == "yes" ]]; then
    ENABLE_NETWORK_POLICIES = ${ENABLE_NETWORK_POLICIES}
  else
    ENABLE_NETWORK_POLICIES="yes"
  fi
  ENABLE_KANIKO="yes"
  if [[ -z "${EKS_K8S_CLUSTER_NAME}" ]]; then
    EKS_K8S_CLUSTER_NAME="${K8S_CLUSTER_NAME}"
  fi
  if [[ -n "${EXPOSE_PORT}" ]] && [[ ${EXPOSE_PORT} == "yes" ]]; then
    EXPOSE_VSYSTEM="yes"
    EXPOSE_VORA_TXC="yes"
    EXPOSE_TEXT_ANALYSIS="yes"
  fi
  if [[ "${VORA_COMMAND}" == "install" ]]; then
    if [[ "${INSTALL_VIA_SLCB}" == "true" ]] || [[ "${USE_SKOPEO}" == "yes" ]]; then
      if [[ "${USE_CUSTOMIZED_SLCB_BINARY}" == "true" ]]; then
        export EKS_DOCKER_REGISTRY_SUFFIX=${K8S_CLUSTER_NAME}
      else 
        export EKS_DOCKER_REGISTRY_SUFFIX="validation-shared"
      fi
      export EKS_VFLOW_DOCKER_REGISTRY_SUFFIX=${K8S_CLUSTER_NAME}
    fi
  fi
elif [ ${1} == "GARDENER-AWS" ]; then
  DEPLOY_DOCKER_CLUSTER="false"
  ENABLE_AUTHENTICATION="no"
  VSYSTEM_USE_EXTERNAL_AUTH="yes"
  hosts_file="${ROOT_DIR}/inventories/hosts"
  admin_conf="/infrabox/inputs/${K8S_CREATION_JOB}/admin.conf"
  GARDENER_SHOOT_KUBECONFIG="${admin_conf}"
  KUBE_ADMIN_CONFIG_PATH="${admin_conf}"
  CLOUD_PLATFORM="gardener-aws"
  SHOOT_NAME=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/shoot_name.txt)
  AWS_SECURITY_JSON_FILE="/credential.json"
  GARDENER_AWS_K8S_CLUSTER_NAME=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_bucket.txt) # workaround
  if [[ -z "${GARDENER_AWS_K8S_CLUSTER_NAME}" ]]; then
    GARDENER_AWS_K8S_CLUSTER_NAME="${K8S_CLUSTER_NAME}"
  fi
  ENABLE_NETWORK_POLICIES="yes"
  GARDENER_AWS_REGION="eu-central-1"
  if [[ -n "${EXPOSE_PORT}" ]] && [[ ${EXPOSE_PORT} == "yes" ]]; then
    EXPOSE_VSYSTEM="yes"
    EXPOSE_VORA_TXC="yes"
    EXPOSE_TEXT_ANALYSIS="yes"
  fi
elif [ ${1} == "GARDENER-CCLOUD" ]; then
  DEPLOY_DOCKER_CLUSTER="false"
  ENABLE_AUTHENTICATION="no"
  VSYSTEM_USE_EXTERNAL_AUTH="yes"
  hosts_file="${ROOT_DIR}/inventories/hosts"
  admin_conf="/infrabox/inputs/${K8S_CREATION_JOB}/admin.conf"
  GARDENER_SHOOT_KUBECONFIG="${admin_conf}"
  KUBE_ADMIN_CONFIG_PATH="${admin_conf}"
  ENABLE_STORAGE_CHECKPOINT="yes"
  CLOUD_PLATFORM="gardener-ccloud"
  SHOOT_NAME=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/shoot_name.txt)
  GARDENER_PROJECT_NAME=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/gardener_project_name.txt)
  GARDENER_CCLOUD_K8S_CLUSTER_NAME=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_bucket.txt) # workaround
  if [[ -z "${GARDENER_CCLOUD_K8S_CLUSTER_NAME}" ]]; then
    GARDENER_CCLOUD_K8S_CLUSTER_NAME="${K8S_CLUSTER_NAME}"
  fi
  ENABLE_NETWORK_POLICIES="yes"
  if [[ -n "${EXPOSE_PORT}" ]] && [[ ${EXPOSE_PORT} == "yes" ]]; then
    EXPOSE_VSYSTEM="yes"
    EXPOSE_VORA_TXC="yes"
    EXPOSE_TEXT_ANALYSIS="yes"
  fi
else
  echo "Privisioning type ${1} not supported !"
  echo ${USAGE}
  exit 1
fi


if [[ "${INSTALL_VIA_SLCB}" == "true" ]] && [[ "${USE_CUSTOMIZED_SLCB_BINARY}" == "true" ]]; then
  if [ -z "${SLCB_BINARY_IMAGE}" ] || [ -z "${CUSOTOMIZED_SLCB_TAG}" ]; then
    echo "No image or tag to get slcb binary"
    exit 1
  fi 
  IMAGE="${SLCB_BINARY_IMAGE}:${CUSOTOMIZED_SLCB_TAG}"
  echo "## pulling custom ${IMAGE}"	
  docker pull ${IMAGE}
  container_id=$(docker run -d -it ${IMAGE} /slcb_binary/slcb-linuxx86_64-${CUSOTOMIZED_SLCB_TAG}.exe)
  docker cp $container_id:/slcb_binary /
  docker kill $container_id
fi
if [[ -z "${UNINSTALL_VIA_SLCB}" ]]; then
  if [[ "${USE_SKOPEO}" == "yes" ]] && [[ "${INSTALL_VIA_SLCB}" != "true" ]]; then
    ${ROOT_DIR}/tools/mirror_docker_image_by_skopeo.sh "on_prem"
    if [ $? -ne 0 ]; then
      echo "mirror docker images by skopeo failed, exit!"
      exit 1
    fi
  fi
fi

if [ -n "${EXTRA_INSTALL_PARAMETERS}" ]; then
  echo "export EXTRA_INSTALL_PARAMETERS=${EXTRA_INSTALL_PARAMETERS}" >> ${env_file}
fi

# for upgrade testing
if [ -n "${K8S_CREATION_JOB}" ] && [[ -f /infrabox/inputs/${K8S_CREATION_JOB}/bdh_base_version.sh ]]; then
  source /infrabox/inputs/${K8S_CREATION_JOB}/bdh_base_version.sh
  echo "export BASE_BDH_VERSION=${BASE_BDH_VERSION}" >> ${env_file}

  if [ -n "${TARGET_VERSION_INSTALLATION_OPTIONS}" ]; then
    echo "export EXTRA_INSTALL_PARAMETERS=${TARGET_VERSION_INSTALLATION_OPTIONS}" >> ${env_file}
  fi

  if [[ -n "${VORA_SYSTEM_TENANT_PASSWORD}" ]] && [[ -n "${VORA_PASSWORD}" ]];then
    echo "export VORA_SYSTEM_TENANT_PASSWORD='${VORA_SYSTEM_TENANT_PASSWORD}'" >> ${env_file}
    echo "export VORA_PASSWORD='${VORA_PASSWORD}'" >> ${env_file}
  fi

  if [ -n "$AZURE_DOCKER_LOGIN_USERNAME" ]; then
    echo "export AZURE_DOCKER_LOGIN_USERNAME=${AZURE_DOCKER_LOGIN_USERNAME}" >> ${env_file}
  fi

  if [ -n "$AZURE_DOCKER_LOGIN_ADDRESS" ]; then
    echo "export AZURE_DOCKER_LOGIN_ADDRESS=${AZURE_DOCKER_LOGIN_ADDRESS}" >> ${env_file}
  fi

  if [ -n "$AZURE_DOCKER_LOGIN_PASSWORD" ]; then
    echo "export AZURE_DOCKER_LOGIN_PASSWORD=${AZURE_DOCKER_LOGIN_PASSWORD}" >> ${env_file}
  fi

  if [ ${1} == "AZURE-AKS" ]; then
    k8s_creation_env_file="/infrabox/inputs/${K8S_CREATION_JOB}/env.sh"
    AKS_CLUSTER_NAME=$(cat ${k8s_creation_env_file}| grep VSYSTEM_ENDPOINT |awk -F'//' '{ print $2 }' | awk -F'-aks' '{print $1}')
    #aks cluster name is not same as k8s cluster name on aks.
  fi

  # To remove vora if upgrade DI from 3.2/3.1 to 3.3
  # If the DI contains vora, upgrade will be failed.
  # JIRA ID BDH-17386
  if [[ ${VORA_VERSION: 0: 1} -gt 2 && ${VORA_VERSION: 2: 1} -gt 2 ]]; then
    remove_vora_cluster_from_deployments
  fi
fi

if [ -n "${K8S_CREATION_JOB}" ] && [[ -f /infrabox/inputs/${K8S_CREATION_JOB}/azure_cert_file.sh ]]; then
  source /infrabox/inputs/${K8S_CREATION_JOB}/azure_cert_file.sh
fi 

# get the VSYSTEM_VERSION then download vctl
# the vctl must be avaliable before ansible install
update_env
if ! get_vctl_from_installer; then
  download_vctl
  cp ./vctl /infrabox/output/vctl
fi

#goto the ansible folder before run the ansible command
pushd ${ROOT_DIR}

if [ ! -f ${admin_conf} ];then
  echo "No availiable k8s admin.conf found at : ${admin_conf}"
  exit 1
fi

#
# To fix a issue DIBUGS-14221, we need remove the workaround which for old slcb 1.1.45.
#
# if [[ "${VORA_COMMAND}" == "update" ]]; then
#   kubectl label ns "${NAMESPACE}" app-
#   if [[ ${1} == "AWS-EKS" ]]; then
#     node="$(kubectl -n "${NAMESPACE}" get pod vsystem-vrep-0 -o jsonpath='{.spec.nodeName}')"
#     if [[ -n "${node}" ]]; then
#       echo "vrep scheduled on ${node}"
#       kubectl -n "${NAMESPACE}" patch sts vsystem-vrep --type strategic --patch "{\"spec\": {\"template\": {\"spec\": {\"nodeSelector\": {\"kubernetes.io/hostname\": \"${node}\"}}}}}"
#     fi
#   fi 
# fi

if [[ -n "${OPERATION_TYPE}" ]] && [[ ${OPERATION_TYPE} == "UNINSTALL" ]];then
  if [ ${1} == "MONSOON" ];then
    uninstall_vora "${@}"
  elif [ ${1} == "GKE" ] || [ ${1} == "AZURE-AKS" ] || [ ${1} == "AWS" ] || [ ${1} == "AWS-EKS" ] || [ ${1} == "GARDENER-AWS"|| [ ${1} == "GARDENER-CCLOUD" ]; then
    VORA_COMMAND="uninstall"
    uninstall_vora_on_cloud "${@}"
  fi
  if [ $? -ne 0 ]; then
    copy_log "uninstall"
    ftp_delete
    echo "Uninstall vora failed."
    exit 1
  fi
  copy_log "uninstall"
  ftp_delete
  echo "Uninstall vora successfully."
  exit 0
else
  # make tiller version the same as helm
  if [[ "${INSTALL_VIA_SLCB}" != "true" ]]; then
    #workaround for k8s 1.16
    helm init --output yaml | sed 's@apiVersion: networking.k8s.io/v1@apiVersion: apps/v1@' | sed 's@  replicas: 1@  replicas: 1\n  selector: {"matchLabels": {"app": "helm", "name": "tiller"}}@' | kubectl apply -f -
    helm init --upgrade --force-upgrade
    RETRY=20
    for ((i = 1; i <= ${RETRY}; i++)); do
      helm version
      if [ $? -eq 0 ]; then
        break
      elif [ $i -eq $[${RETRY}/2] ]; then
        #If can't connect helm server in 10 tries, restart tunnelfront pods in kube-system, then have another 10 tries
        tunnelfront_pod_name=$(kubectl get pods -o custom-columns=NAME:.metadata.name -n kube-system | grep tunnelfront)
        if [[ -n "${tunnelfront_pod_name}" ]]; then
          kubectl delete pod ${tunnelfront_pod_name} -n kube-system
        fi
      elif [ $i -eq ${RETRY} ]; then
        pods_name=$(kubectl get pods -o custom-columns=NAME:.metadata.name -n kube-system | grep tiller)
        pods_describe=""
        pods_log=""
        if [[ -n "${pods_name}" ]]; then
          pods_describe=$(kubectl describe pods/${pods_name} -n kube-system)
          pods_log=$(kubectl logs ${pods_name} -n kube-system)
        fi
        cat << EOF >> /infrabox/upload/archive/error_msg.log
health_check: Cannot Connect to Tiller
=============System pods info==============:
$(kubectl get pods -n kube-system)
=============Tiller pods describe info==============:
${pods_describe}
=============Tiller pods log info==============:
${pods_log}
EOF
        die "### [level=warning] helm version command failed. Most probably tiller did not come up at time. Exit installer"
      else
        sleep 60
      fi
    done
  fi

  if [ ${1} == "MONSOON" ];then
    deploy_vora_push_validation "${@}"
  elif [ ${1} == "GKE" ] || [ ${1} == "AWS" ] || [ ${1} == "AZURE-AKS" ] || [ ${1} == "AWS-EKS"  ] || [ ${1} == "GARDENER-AWS" || [ ${1} == "GARDENER-CCLOUD" ]; then
    bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${ROOT_DIR}/playbooks/vora/install-vora-on-cloud.yml --tags=${VORA_COMMAND}"
  fi
  if [ $? -ne 0 ]; then
      dump_k8s_cluster_info
      copy_log "installation"
      echo "Install vora failed."
      exit 1
  fi
  copy_log "installation"
  #generate env.sh
  echo "namespace is: ${K8S_INSTALLER_NAMESPACE}"
  echo "host master is ${master_host}"
  #generate env.sh
  if [ ${1} == "GKE" ]; then
    vsystem_port=$(unset http_proxy; unset https_proxy; kubectl get service vsystem-ext -n ${K8S_INSTALLER_NAMESPACE} -o=custom-columns=:.spec.ports[0].nodePort | grep -v '^$')
  else
    # for gardeneri, aws, aks, there is no NODEPORT, use 443 instead
    vsystem_port="443"
  fi

  if [ ${1} == "MONSOON" ] || [ ${1} == "AZURE-AKS" ] || [ ${1} == "AWS" ] || [ ${1} == "GKE" ] || [ ${1} == "AWS-EKS" ] || [ ${1} == "GARDENER-AWS" || [ ${1} == "GARDENER-CCLOUD"  ] || [ ${1} == "DHAAS-AWS" ]; then
      echo "## searching summary.log"
      summary_file=$(find . -name "*summary.log")
      cat ${summary_file}
      vsystem_endpoint=$(cat ${summary_file} | grep "datahub launch-pad endpoint" | awk -F' ' '{ print $4 }')
      vora_tenant=$(cat ${summary_file} | grep "datahub user tenant name" | awk -F' ' '{ print $5 }')
      vora_username=$(cat ${summary_file} | grep "datahub user/system tenant user" | awk -F' ' '{ print $5 }')
      vora_system_tenant_password=$(cat ${summary_file} | grep "datahub system tenant password" | awk -F' ' '{ print $5 }')
      vora_password=$(cat ${summary_file} | grep "datahub user tenant password" | awk -F' ' '{ print $5 }')
      container_registry_address=$(cat ${summary_file} | grep "container registry address" | awk -F' ' '{ print $5 }')
      container_registry_username=$(cat ${summary_file} | grep "container registry username" | awk -F' ' '{ print $5 }')
      container_registry_password=$(cat ${summary_file} | grep "container registry password" | awk -F' ' '{ print $5 }')
      di_backup_path_prefix=$(cat ${summary_file} | grep "di backup path prefix" | awk -F' ' '{ print $NF }')
  fi

  master_host=$(grep 'server' ${admin_conf} | awk '{print $2}' | cut -d'/' -f3 | cut -d':' -f1)
  if [ ${1} == "MONSOON" ]; then
    node_host=$(host $master_host | cut -d' ' -f5 | sed 's/.\{1\}$//') # get hostname by ip
  elif [ ${1} == "GKE" ] ; then
    node_host=$(kubectl get nodes -o wide | grep -m1 'Ready' | awk '{print $6}')
  elif [ ${1} == "AZURE-AKS" ] || [ ${1} == "AWS" ] || [ ${1} == "AWS-EKS" ] || [ ${1} == "GARDENER-AWS" ] || [ ${1} == "GARDENER-CCLOUD" ]; then
    # remove the leading https:// and the suffix :443
    temp_str=$(echo ${vsystem_endpoint#*//})
    node_host=$(echo ${temp_str%:*})
  fi

  if [ -z "$VORA_PACKAGE" ]; then
      summary_file=$(find . -name "*summary.log")
      vora_path=$(cat ${summary_file} | grep "datahub package url" | awk -F' ' '{ print $4 }')
  fi

  if [ -f "$VORA_ENV_FILE" ]; then
    cp ${VORA_ENV_FILE} ${env_file}
  fi

  if [[ -f "/infrabox/inputs/${K8S_CREATION_JOB}/k8s_version.txt" ]]; then
    K8S_VERSION=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_version.txt)
  fi
  echo "export RELEASEPACK_VERSION=${VORA_VERSION}" >> ${env_file}
  cat << EOF >> ${env_file}
export VORA_TENANT="${vora_tenant}"
export VORA_USERNAME="${vora_username}"
export VORA_SYSTEM_TENANT=system
export VORA_SYSTEM_TENANT_PASSWORD='${vora_system_tenant_password}'
export VORA_PASSWORD='${vora_password}'
export PROVISION_PLATFORM="${1}"
export NODE_HOST="${node_host}"
export VSYSTEM_PORT="${vsystem_port}"
export VSYSTEM_ENDPOINT="${vsystem_endpoint}"
export NAMESPACE="${K8S_INSTALLER_NAMESPACE}"
export KUBECONFIG="/infrabox/inputs/${K8S_CREATION_JOB}/admin.conf"
export K8S_VERSION="${K8S_VERSION}"
export K8S_CLUSTER_NAME="${K8S_CLUSTER_NAME}"
export CONTAINER_REGISTRY_ADDRESS="${container_registry_address}"
export DI_BACKUP_PATH_PREFIX="${di_backup_path_prefix}"
EOF

  if [ -n "$vora_path" ]; then
    echo "export VORA_MILESTONE_PATH=${vora_path}" >> ${env_file}
  fi
  if [ -n "$GCP_DOCKER_REGISTRY_SUFFIX" ]; then
    echo "export GCP_DOCKER_REGISTRY_SUFFIX=${GCP_DOCKER_REGISTRY_SUFFIX}" >> ${env_file}
  fi
  if [ -n "${container_registry_username}" ]; then
    echo "export CONTAINER_REGISTRY_USERNAME=${container_registry_username}" >> ${env_file}
  fi
  if [ -n "${container_registry_password}" ]; then
    echo "export CONTAINER_REGISTRY_PASSWORD=${container_registry_password}" >> ${env_file}
  fi
  source ${env_file}
  echo "Install vora successfully."

  if ! vctl --help >/dev/null 2>&1; then
    echo "## Warning! No vctl binary found! Cannot create vflow instance!"
  else
    echo "##Create vflow instance"
    RETRY=10
    for ((i = 1; i <= ${RETRY}; i++)); do
      vctl login ${vsystem_endpoint} ${vora_tenant} ${vora_username} -p ${vora_password} --insecure
      # change tracer log level to debug
      vctl parameter set vflow.traceLevel debug --tenant=${vora_tenant}
      vctl scheduler start pipeline-modeler
      if [ $? -ne 0 ]; then
        sleep 30s # wait pods up
      fi
      VFLOW_POD=$(kubectl get pods -l vora-component=vflow,vsystem.datahub.sap.com/user=${VORA_USERNAME},vsystem.datahub.sap.com/tenant=${VORA_TENANT} -n ${K8S_INSTALLER_NAMESPACE} -o go-template --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')
      if [ -z "${VFLOW_POD}" ]; then
        if [ $i -lt ${RETRY} ]; then
          echo "create instance failed. Retry..."
          sleep 30s
          continue
        else
          echo "### [level=warning] Create vflow instance failed!"
        fi
      else
        vctl parameter set vflow.traceLevel info --tenant=${vora_tenant}
        break
      fi
    done
  fi

  echo "## BDH Health Check"

  source ${env_file}
  echo "skip cluster check"
  export SKIP_CLUSTER_CHECK="yes"
  python /project/bdh_health_check.py
  HEALTH_CHECK_RESULT=$?

  if [[ "${USE_CUSTOMIZED_SLCB_BINARY}" == "true" ]]; then
    echo "Skip load db driver and create data lack connection in SLCB validation"
    exit $HEALTH_CHECK_RESULT
  fi

  def_conn --action=load_driver
  LOAD_DB_DRIVER_RESULT=$?

  if [ ${1} == "AWS-EKS" ] && [ "${ENABLE_NETWORK_POLICIES}" == "yes" ]; then
    echo "## install netpol logger..."
    create_calico_netpol_logger
    echo "## install netpol logger is done..."
  fi

  # skip DI_DATA_LAKE preparation in backup/restore scenario since this connection is not b/r testing scope
  # prepare DI_DATA_LAKE after installtion
  if [[ -n "${VORA_KUBE_SUFFIX}" ]] && [[ "${VORA_KUBE_SUFFIX}" == "DI-Assembly" ]] && ([[ "${ENABLE_BACKUP}" != "true" ]] && [[ "${ENABLE_RESTORE}" != "true" ]]); then
    echo "## creating DI_DATA_LAKE connection..."
    python ${ROOT_DIR}/tools/create_connection.py "${vsystem_endpoint}" ${1} "${AUTH_HEADER}" ${vora_tenant} ${vora_username} ${vora_password} "SDL"
    DI_DATA_LAKE_CONNECTION_CREATION_RESULT=$?
    if [ $DI_DATA_LAKE_CONNECTION_CREATION_RESULT != 0 ]; then
      echo "## DI DATALAKE CONNECTION creation failed!"
      exit 1
    fi
  fi

  cat ${env_file}
  cp ${env_file} /infrabox/upload/archive/

  # dump the k8s
  dump_k8s_cluster_info

  if [ $HEALTH_CHECK_RESULT != 0 ]; then
    echo "## Health Check failed!"
    exit 1
  fi
  echo "## Health Check is done!"

  if [ $LOAD_DB_DRIVER_RESULT -ne 0 ]; then
    echo "## Load db driver failed!"
    exit 1
  fi
  echo "## Load db deriver is done!"
fi

