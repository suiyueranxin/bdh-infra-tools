#!/bin/bash
#usage: just call this script with one parameter specified the cloud provisioning type
#now just support following:
#  CCLOUD
#  MONSOON
#all the pamameter needed when run ansible will be handle in function in jenkins-common.sh

USAGE="$0 CCLOUD|MONSOON"

if [ $# -ne 1 ];then
   echo ${USAGE}
   exit 1
fi

export ROOT_DIR=$(dirname ${BASH_SOURCE[0]})/../
#goto the ansible folder before run the ansible command
pushd ${ROOT_DIR}

#source common function for parser jenkins parameters
source ${ROOT_DIR}/tools/jenkins-common.sh

#set different inventory file for ccloud and monsoon
if [ ${1} == "CCLOUD" ];then
   hosts_file="${ROOT_DIR}/inventories/ccloud_hosts"
elif [ ${1} == "MONSOON" ];then
   hosts_file="${ROOT_DIR}/inventories/monsoon_hosts"
else
   echo "Privisioning type ${1} not supported !"
   echo ${USAGE}
   exit 1
fi
token_deploy_playbook="${ROOT_DIR}/playbooks/cloud/cluster-add-token.yml"

# this also skip destroying the cluster if deploy token failed, user still can use the k8s cluster
bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${token_deploy_playbook}"

#consolidate all infos after install k8s and will send email with this file
if [ ! -d ${WORKSPACE}/${BUILD_NUMBER}/ ];then
   mkdir ${WORKSPACE}/${BUILD_NUMBER}/
fi
cp ${hosts_file} ${WORKSPACE}/${BUILD_NUMBER}/result


echo "All task output and infos can be found at : ${WORKSPACE}/${BUILD_NUMBER}/result"
#currently we don't have a summary result when finish all the ansible task, so in jenkins side , we can user this resuslt file
#to send out this result file to user via email
