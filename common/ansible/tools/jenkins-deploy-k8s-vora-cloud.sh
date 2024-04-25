#!/bin/bash

#this script should work together with jenkins jobs with pamameter as : https://vas-jenkins.mo.sap.corp:8443/view/Cluster_Deployment/job/Vora-21-With-Ccloud-k8s-Deployment/
#usage: just call this function with one parameter specified the cloud provisioning type
#now just support following:
#  CCLOUD
#  MONSOON

USAGE="$0 GARDENER|GKE|AZURE|AZURE-AKS|AWS-EKS|GARDENER-CCLOUD"

if [ $# -ne 1 ];then
   echo ${USAGE}
   exit 1
fi

export ROOT_DIR=$(dirname ${BASH_SOURCE[0]})/../

#source common function for parser jenkins parameters
source ${ROOT_DIR}/tools/jenkins-cluster-utils.sh

#set this when deploy cluster without docker
DEPLOY_DOCKER_CLUSTER="false"
ENABLE_AUTHENTICATION="no"  # not need after 2.1.3* , but we need it to be specified for enable kerberos or not
ENABLE_VORA_INSTALLATION=${ENABLE_VORA_INSTALLATION:-"false"}

#set project name
PROJECT_NAME="k8s"

#set different inventory file for different provisioning type
if [ ${1} == "GARDENER-AWS" ];then
  hosts_file="${ROOT_DIR}/inventories/hosts"
  cluster_playbook="${ROOT_DIR}/playbooks/cloud/gardener/create-gardener-shoot.yml"
  cluster_destroy_playbook="${ROOT_DIR}/playbooks/cloud/gardener/destroy-gardener-shoot.yml"
  cluster_admin_cfg="${ROOT_DIR}/playbooks/cloud/gardener/KUBECONFIG"
  CLOUD_PLATFORM="gardener-aws"
elif [ ${1} == "GKE" ];then
  hosts_file="${ROOT_DIR}/inventories/hosts"
  cluster_playbook="${ROOT_DIR}/playbooks/cloud/gcloud/deploy_k8s.yaml"
  cluster_admin_cfg="${ROOT_DIR}/playbooks/cloud/gcloud/KUBECONFIG"
  cluster_destroy_playbook="${ROOT_DIR}/playbooks/cloud/gcloud/remove_k8s.yaml"
  CLOUD_PLATFORM="gke"
elif [ ${1} == "AZURE" ];then
  hosts_file="${ROOT_DIR}/inventories/azure_hosts"
  cluster_playbook="${ROOT_DIR}/playbooks/cloud/azure/create-azure-k8s-cluster.yml"
  cluster_admin_cfg="${ROOT_DIR}/playbooks/cloud/azure/KUBECONFIG"
  cluster_destroy_playbook="${ROOT_DIR}/playbooks/cloud/azure/destroy-azure-k8s-cluster.yml"
  CLOUD_PLATFORM="azure"
elif [ ${1} == "AWS" ];then
  hosts_file="${ROOT_DIR}/inventories/hosts"
  cluster_playbook="${ROOT_DIR}/playbooks/cloud/kops/create-kops-cluster.yml"
  cluster_admin_cfg="${ROOT_DIR}/playbooks/cloud/kops/KUBECONFIG"
  cluster_destroy_playbook="${ROOT_DIR}/playbooks/cloud/kops/destroy-kops-cluster.yml"
  CLOUD_PLATFORM="kops"
elif [ ${1} == "AZURE-AKS" ];then
  hosts_file="${ROOT_DIR}/inventories/hosts"
  cluster_playbook="${ROOT_DIR}/playbooks/cloud/azure/create-aks-cluster.yml"
  cluster_admin_cfg="${ROOT_DIR}/playbooks/cloud/azure/KUBECONFIG"
  cluster_destroy_playbook="${ROOT_DIR}/playbooks/cloud/azure/destroy-aks-cluster.yml"
  CLOUD_PLATFORM="azure-aks"
elif [ ${1} == "AWS-EKS" ];then
  hosts_file="${ROOT_DIR}/inventories/eks_hosts"
  cluster_playbook="${ROOT_DIR}/playbooks/cloud/eks/eks_deploy_k8s.yaml"
  cluster_admin_cfg="${ROOT_DIR}/playbooks/cloud/eks/KUBECONFIG"
  cluster_destroy_playbook="${ROOT_DIR}/playbooks/cloud/eks/eks_destroy_k8s.yaml"
  CLOUD_PLATFORM="eks"
else
  echo "Privisioning type ${1} not supported !"
  echo ${USAGE}
  exit 1
fi

#set cluster master and worker prefix
set_cluster_node_prefix

#goto the ansible folder before run the ansible command
pushd ${ROOT_DIR}
#if [ ${VORA_COMMAND} == "install" ]; then
#  deploy_k8s_cloud "${@}"
#fi

deploy_vora_cloud "${@}"

if [ -f ${hosts_file} ];then
   cp ${hosts_file} ${OUTPUT_DIR}/host.txt
   cp ${hosts_file} /infrabox/upload/archive
fi

if [ -f ${cluster_admin_cfg} ];then
   cp ${cluster_admin_cfg} ${OUTPUT_DIR}/KUBECONFIG.txt
   cp ${cluster_admin_cfg} /infrabox/upload/archive
fi

if [ -f ${ROOT_DIR}/playbooks/vora/vora_installation.log ];then
  cp ${ROOT_DIR}/playbooks/vora/vora_installation.log  ${OUTPUT_DIR}/vora_installation.log
  cp ${ROOT_DIR}/playbooks/vora/vora_installation.log /infrabox/upload/archive
fi

if [ -f ${ROOT_DIR}/playbooks/vora/summary.log ];then
  cp ${ROOT_DIR}/playbooks/vora/summary.log  ${OUTPUT_DIR}/summary.log
  cp ${ROOT_DIR}/playbooks/vora/summary.log  /infrabox/upload/archive
fi

if [ -f ${ROOT_DIR}/playbooks/vora/install_logs_folder.zip ];then
  cp ${ROOT_DIR}/playbooks/vora/install_logs_folder.zip  ${OUTPUT_DIR}/install_logs_folder.zip
  cp ${ROOT_DIR}/playbooks/vora/install_logs_folder.zip  /infrabox/upload/archive
fi

