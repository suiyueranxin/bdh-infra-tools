#!/bin/bash

#this script should work together with jenkins jobs with pamameter as : https://vas-jenkins.mo.sap.corp:8443/view/Cluster_Deployment/job/Hadoop-Vora-2.x-Cluster-Deployment/
#usage: just call this fuction with one parameter specified the cloud provisioning type
#now just support following:
#  CCLOUD
#all the pamameter needed when run ansible will be handle in function in jenkins-common.sh

USAGE="$0 MONSOON"

  if [ $# -ne 1 ];then
    echo ${USAGE}
    exit 1
  fi

#source common function for parser jenkins parameters
export ROOT_DIR=$(dirname ${BASH_SOURCE[0]})/../
source ${ROOT_DIR}/tools/jenkins-cluster-utils.sh

trap 'cleanup ${hosts_file} ${cluster_destroy_playbook};exit 1' ERR

#set project name
PROJECT_NAME="hadoop"
#set cluster master and worker prefix
set_cluster_node_prefix

if [ ${1} == "MONSOON" ];then
    hosts_file="${ROOT_DIR}/inventories/monsoon_hadoop_hosts"
    cluster_playbook="${ROOT_DIR}/playbooks/cloud/monsoon/create-monsoon-cluster.yml"
    cluster_destroy_playbook="${ROOT_DIR}/playbooks/cloud/monsoon/destroy-monsoon-cluster.yml"
    hadoop_playbook="${ROOT_DIR}/playbooks/hadoop/bootstrap-hadoop-cluster.yml"

    if [ "${CLUSTER_MANAGER}" == "mapr" ]; then
        hosts_file="${ROOT_DIR}/inventories/monsoon_hadoop_mapr_hosts"
    fi
else
    echo "Privisioning type ${1} not supported !"
    echo ${USAGE}
    exit 1
fi
#goto the ansible folder before run the ansible command
pushd ${ROOT_DIR}

${ROOT_DIR}/fetch-external-deps.sh

deploy_hadoop "${@}"

cp ${hosts_file} ${OUTPUT_DIR}
