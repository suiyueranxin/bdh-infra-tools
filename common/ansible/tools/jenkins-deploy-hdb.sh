#!/bin/bash
#set -e
#usage: just call this script with one parameter specified the cloud provisioning type
trap 'cleanup ${hosts_file} ${cluster_destroy_playbook};exit 1' ERR

USAGE="$0 MONSOON [TESTPACK|HANA-XS|HANA-XS-TESTPACK]"

echo "Calling jenkins-deploy-hdb.sh ..."
if [ $# -lt 1 ];then
   echo ${USAGE}
   exit 1
fi
export ROOT_DIR=$(dirname ${BASH_SOURCE[0]})/../

#goto the ansible folder before run the ansible command
pushd ${ROOT_DIR}

if [ ${1} == "MONSOON" ]; then
   EC2_URL=https://ec2-${MONSOON_REGION}.api.monsoon.mo.sap.corp
   NUMBER_OF_WORKERS=0
fi

#set project name
PROJECT_NAME="hanabdh"

#source common function for parser jenkins parameters
source ${ROOT_DIR}/tools/jenkins-common.sh

#set cluster master and worker prefix
set_cluster_node_prefix

#set this when deploy cluster without docker
export DEPLOY_DOCKER_CLUSTER="false"

echo "prepare ansible-playbook and hosts ..."
#set different inventory file for ccloud and monsoon
if [ ${1} == "MONSOON" ];then
  hosts_file="${ROOT_DIR}/inventories/monsoon_hana_hosts"
  host_playbook="${ROOT_DIR}/playbooks/cloud/monsoon/create-monsoon-cluster.yml"
  volume_playbook="${ROOT_DIR}/playbooks/cloud/monsoon/monsoon-extend-volume.yml"
  cluster_destroy_playbook="${ROOT_DIR}/playbooks/cloud/monsoon/destroy-monsoon-cluster.yml"
  hdb_playbook="${ROOT_DIR}/playbooks/hana/install-hana.yml"
  test_playbook="${ROOT_DIR}/playbooks/hana/install-testpack.yml"
else
  echo "Privisioning type ${1} not supported !"
  echo ${USAGE}
  exit 1
fi

trap 'echo "## deploy HANA failed, please see detail info from previously log section ...";echo "## start trying to do cleanup ...";cleanup ${hosts_file} ${cluster_destroy_playbook};exit 1' ERR
echo "ansible-playbook starting ..."

#call ansible playbook for create instances for hana installation
bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${host_playbook}"

# this also skip destroying the cluster if deploy token failed, user still can use the k8s cluster
#if ( ! bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${ROOT_DIR}/playbooks/cloud/cluster-add-token.yml" ); then
#  echo "\nDeploy cluster token failed!" >> ${WORKSPACE}/${BUILD_NUMBER}/result
#fi

if [ ${1} == "MONSOON" ]; then
   bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${volume_playbook}"
fi

#call ansible playbook for install hana
bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${hdb_playbook}"

#call ansible playbook for install testpack
if [ $# -gt 1 ];then
  if [ ${2} == "TESTPACK" ]; then
     bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${test_playbook}"
  fi
fi

if [ -f ${hosts_file} ];then
  cp ${hosts_file} ${OUTPUT_DIR}/hosts.txt
fi

if [ -f ${ROOT_DIR}/playbooks/hana/hdbinst.log ];then
  cp ${ROOT_DIR}/playbooks/hana/hdbinst.log  ${OUTPUT_DIR}/hdbinst.log
  cp ${ROOT_DIR}/playbooks/hana/hdbinst.log /infrabox/upload/archive
fi

if [ -f ${ROOT_DIR}/playbooks/hana/summary.log ];then
  cp ${ROOT_DIR}/playbooks/hana/summary.log  ${OUTPUT_DIR}/summary.log
  cp ${ROOT_DIR}/playbooks/hana/summary.log  /infrabox/upload/archive
fi

if [ -f ${ROOT_DIR}/playbooks/hana/install_logs_folder.zip ];then
  cp ${ROOT_DIR}/playbooks/hana/install_logs_folder.zip  ${OUTPUT_DIR}/install_logs_folder.zip
  cp ${ROOT_DIR}/playbooks/hana/install_logs_folder.zip  /infrabox/upload/archive
fi
