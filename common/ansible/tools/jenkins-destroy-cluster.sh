#!/bin/bash
#usage: just call this script with one parameter specified the cloud provisioning type
#now just support following:
#  CCLOUD
#  MONSOON
#all the pamameter needed when run ansible will be handle in function in jenkins-common.sh

USAGE="$0 CCLOUD|MONSOON|AWS"

if [ $# -ne 1 ];then
   echo ${USAGE}
   exit 1
fi

export ROOT_DIR=$(dirname ${BASH_SOURCE[0]})/../
#goto the ansible folder before run the ansible command
pushd ${ROOT_DIR}

#source common function for parser jenkins parameters
source ${ROOT_DIR}/tools/jenkins-common.sh

#set different inventory file for ccloud or monsoon or aws
if [ ${1} == "CCLOUD" ];then
   hosts_file="${ROOT_DIR}/inventories/ccloud_hosts"
   destroy_cluster_playbook="${ROOT_DIR}/playbooks/cloud/ccloud/destroy-ccloud-nodes.yml"
elif [ ${1} == "MONSOON" ];then
   hosts_file="${ROOT_DIR}/inventories/monsoon_hosts"
   destroy_cluster_playbook="${ROOT_DIR}/playbooks/cloud/monsoon/destroy-monsoon-cluster.yml"
elif [ ${1} == "AWS" ];then
   hosts_file="${ROOT_DIR}/inventories/hosts"
   destroy_cluster_playbook="${ROOT_DIR}/playbooks/cloud/kops/destroy-kops-cluster.yml"
   CLOUD_PLATFORM="kops"
elif [ ${1} == "AZURE-AKS" ];then
   hosts_file="${ROOT_DIR}/inventories/hosts"
   destroy_cluster_playbook="${ROOT_DIR}/playbooks/cloud/azure/destroy-aks-cluster.yml"
   CLOUD_PLATFORM="azure-aks"
elif [ ${1} == "GARDENER-AWS" ];then
   hosts_file="${ROOT_DIR}/inventories/hosts"
   destroy_cluster_playbook="${ROOT_DIR}/playbooks/cloud/gardener/destroy-gardener-shoot.yml"
   CLOUD_PLATFORM="gardener-aws"
else
   echo "Privisioning type ${1} not supported !"
   echo ${USAGE}
   exit 1
fi

if [ -z "$SERVER_URL" ];then
    base_url='https://mo-18fcfba33.mo.sap.corp:31355'
else
    base_url=$SERVER_URL
fi

#set cluster master and worker prefix
set_cluster_node_prefix

email_string=$(echo ${EMAIL%%@*} | sed 's/\./-/g')
cluster_name=${email_string}-${BUILD_NUMBER}
token=$(curl -ikL -d "{\"username\":\"${SYS_ACCOUNT}\", \"password\":\"${SYS_PASSWORD}\"}" -H "Content-Type: application/json"\
         -X POST $base_url/api/v1/user/I349575 | grep token | awk -F'"' '{ print $4 }')

# this also skip destroying the cluster if deploy token failed, user still can use the k8s cluster
bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${destroy_cluster_playbook}"

if [ $? -eq 0 ];then
   curl -H "Authorization: Bearer $token" -ikL -X PATCH $base_url/api/v1/clusters/k8s/status/${cluster_name}/removed
   curl -H "Authorization: Bearer $token" -ikL -X PATCH $base_url/api/v1/clusters/bdh/status/${cluster_name}/removed
   echo "Delete cluster successfully."
else
   curl -H "Authorization: Bearer $token" -ikL -X PATCH $base_url/api/v1/clusters/k8s/status/${cluster_name}/error
   curl -H "Authorization: Bearer $token" -ikL -X PATCH $base_url/api/v1/clusters/bdh/status/${cluster_name}/error
   echo "Delete cluster failed."
fi

echo "All task output and infos can be found at : ${WORKSPACE}/${BUILD_NUMBER}/result"
#currently we don't have a summary result when finish all the ansible task, so in jenkins side , we can user this resuslt file
#to send out this result file to user via email
