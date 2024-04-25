#!/bin/bash

#this script should work together with jenkins jobs with pamameter as : https://vas-jenkins.mo.sap.corp:8443/view/Cluster_Deployment/job/Vora-21-With-Ccloud-k8s-Deployment/
#usage: just call this function with one parameter specified the cloud provisioning type
#now just support following:
#  CCLOUD
#  MONSOON

USAGE="$0 CCLOUD|MONSOON"

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
PROJECT_NAME="k8svora"
#set cluster master and worker prefix
set_cluster_node_prefix

#set different inventory file for different provisioning type
if [ ${1} == "CCLOUD" ];then
  hosts_file="${ROOT_DIR}/inventories/ccloud_hosts"
  cluster_playbook="${ROOT_DIR}/playbooks/cloud/ccloud/create-ccloud-cluster.yml"
  dns_playbook="${ROOT_DIR}/playbooks/cloud/ccloud/create-dns-record.yml"
  cluster_destroy_playbook="${ROOT_DIR}/playbooks/cloud/ccloud/destroy-ccloud-nodes.yml"
  volume_playbook="${ROOT_DIR}/playbooks/cloud/ccloud/ccloud-add-volume.yml"
elif [ ${1} == "MONSOON" ];then
  hosts_file="${ROOT_DIR}/inventories/monsoon_hosts"
  cluster_playbook="${ROOT_DIR}/playbooks/cloud/monsoon/create-monsoon-cluster.yml"
  volume_playbook="${ROOT_DIR}/playbooks/cloud/monsoon/monsoon-extend-volume.yml"
  cluster_destroy_playbook="${ROOT_DIR}/playbooks/cloud/monsoon/destroy-monsoon-cluster.yml"
else
  echo "Privisioning type ${1} not supported !"
  echo ${USAGE}
  exit 1
fi

#goto the ansible folder before run the ansible command
pushd ${ROOT_DIR}

if [ ${VORA_COMMAND} == "install" ];then
  deploy_k8s "${@}"
  if [ -f ${ROOT_DIR}/playbooks/k8s/KUBECONFIG ];then
    cp ${ROOT_DIR}/playbooks/k8s/KUBECONFIG ${OUTPUT_DIR}/KUBECONFIG.txt
    cp ${ROOT_DIR}/playbooks/k8s/KUBECONFIG /infrabox/upload/archive
  fi
  if [ -f ${hosts_file} ];then
    cp ${hosts_file} ${OUTPUT_DIR}/hosts.txt
  fi
fi

deploy_vora "${@}"
if [ -f ${ROOT_DIR}/playbooks/k8s/KUBECONFIG ];then
  cp ${ROOT_DIR}/playbooks/k8s/KUBECONFIG ${OUTPUT_DIR}/KUBECONFIG.txt
  cp ${ROOT_DIR}/playbooks/k8s/KUBECONFIG /infrabox/upload/archive
fi
if [ -f ${hosts_file} ];then
  cp ${hosts_file} ${OUTPUT_DIR}/hosts.txt
fi
if [ -f ${ROOT_DIR}/playbooks/vora/vora_installation.log ];then
  cp ${ROOT_DIR}/playbooks/vora/vora_installation.log  ${OUTPUT_DIR}/vora_installation.log
  cp ${ROOT_DIR}/playbooks/vora/vora_installation.log  /infrabox/upload/archive
fi
if [ -f ${ROOT_DIR}/playbooks/vora/summary.log ];then
  cp ${ROOT_DIR}/playbooks/vora/summary.log  ${OUTPUT_DIR}/summary.log
  cp ${ROOT_DIR}/playbooks/vora/summary.log /infrabox/upload/archive
fi
if [ -f ${ROOT_DIR}/playbooks/vora/install_logs_folder.zip ];then
  cp ${ROOT_DIR}/playbooks/vora/install_logs_folder.zip  ${OUTPUT_DIR}/install_logs_folder.zip
  cp ${ROOT_DIR}/playbooks/vora/install_logs_folder.zip  /infrabox/upload/archive
fi
