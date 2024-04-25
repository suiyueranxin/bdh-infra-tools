#!/bin/bash

export ROOT_DIR=$(dirname ${BASH_SOURCE[0]})/../
#source common function for parser jenkins parameters
source ${ROOT_DIR}/tools/jenkins-common.sh

function deploy_hadoop(){

  trap 'echo "deploy hadoop failed ...";cleanup ${hosts_file} ${cluster_destroy_playbook};exit 1' ERR
  #trap 'echo "deploy hadoop failed ...";exit 1' ERR

  #call ansible playbook for create instances cluster
  bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${cluster_playbook}"

  #call ansible playbook for install hadoop
  bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${hadoop_playbook}"
}

function deploy_k8s(){

  trap 'echo "## deploy k8s failed, please see detail info from previously log section ...";echo "## start trying to do cleanup ...";cleanup ${hosts_file} ${cluster_destroy_playbook};exit 1' ERR

  echo "## call ansible playbook for create instances cluster "
  bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${cluster_playbook}"

  if [ ${1} == "CCLOUD" ];then
    echo "## call ansible playbook for create dns address on master node at ccloud only "
    [ -n "$dns_playbook" ] && bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${dns_playbook}"
  fi

  echo "## call ansible playbook for add additional volume"
  bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${volume_playbook}"

  echo "## call ansible playbook for install k8s"
  bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${ROOT_DIR}/playbooks/k8s/install-k8s.yml"

}
function deploy_vora(){

  #trap 'echo "## deploy vora failed ...";cleanup ${hosts_file} ${cluster_destroy_playbook};exit 1' ERR
  #install vora if user specified at jenkins
  if [ $ENABLE_VORA_INSTALLATION == "true" ];then
    echo "## install vora and bdh at k8s cluster ..."    
    if ( ! bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${ROOT_DIR}/playbooks/vora/install-vora-on-kubernetes.yml --tags=${VORA_COMMAND}" ); then
      echo "\nVora installation failed! Please check the installation log for more information"
      if [ ! -f ${ROOT_DIR}/playbooks/vora/vora_installation.log ];then
        echo "Vora installation failed ... even the install.sh didn't be launched correctly..." > ${ROOT_DIR}/playbooks/vora/vora_installation.log
      fi
    fi
  fi
}

function deploy_vora_push_validation(){
  echo "## install vora at k8s cluster ..."
  bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${ROOT_DIR}/playbooks/vora/install-vora-on-kubernetes.yml --tags=${VORA_COMMAND}"
}

function uninstall_vora(){
  echo "## uninstall vora at k8s cluster ..."
  bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${ROOT_DIR}/playbooks/vora/uninstall-vora-on-kubernetes.yml"
}

function uninstall_vora_on_cloud(){
  echo "## uninstall vora at k8s cluster on cloud ..."
  bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${ROOT_DIR}/playbooks/vora/uninstall-vora-on-cloud.yml --tags=${VORA_COMMAND}"
}

function deploy_k8s_cloud(){

  trap 'echo "## deploy k8s failed, please see detail info from previously log section ...";echo "## start trying to do cleanup ...";cleanup ${hosts_file} ${cluster_destroy_playbook};exit 1' ERR

  echo "## call ansible playbook for create k8s at cloud "
  bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${cluster_playbook}"
}
function deploy_vora_cloud(){
  #trap 'echo "## deploy vora failed ...";cleanup ${hosts_file} ${cluster_destroy_playbook};exit 1' ERR

  if [ $ENABLE_VORA_INSTALLATION == "true" ];then
    echo "## call ansible playbook for install vora on k8s at cloud"
    if ( ! bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${ROOT_DIR}/playbooks/vora/install-vora-on-cloud.yml --tags=${VORA_COMMAND}" ); then
      echo "\nVora installation failed! Please check the installation log for more information"
      if [ ! -f ${ROOT_DIR}/playbooks/vora/vora_installation.log ];then
        echo "Vora installation failed ... even the install.sh didn't be launched correctly..." > ${ROOT_DIR}/playbooks/vora/vora_installation.log
      fi
    fi
  fi
}

function vora_krb_hdp_deploy(){
    trap 'echo "deploy hadoop kerberos configuration for vora installation failed ...";exit 1' ERR
    bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${vora_krb_conf_deploy_playbook}"
}

function deploy_all_bdh(){

  #set this when deploy cluster without docker
  DEPLOY_DOCKER_CLUSTER="false"
  #set project name
  PROJECT_NAME="hadoop"
  #set cluster master and worker prefix
  set_cluster_node_prefix
  NUMBER_OF_WORKERS=${HDP_NUMBER_OF_WORKERS}
  deploy_hdp "${@}"
  cp ${hosts_file} ${hosts_file}_hdp
  if [ ${ENABLE_VORA_INSTALLATION} == "true" ];then
    #set project name
    PROJECT_NAME="k8svora"
    #set cluster master and worker prefix
    set_cluster_node_prefix
    NUMBER_OF_WORKERS=${VORA_NUMBER_OF_WORKERS}
    deploy_k8s "${@}"
    if [ ${ENABLE_AUTHENTICATION} == "yes" ];then
      vora_krb_hdp_deploy "${@}"
    fi
    deploy_vora "${@}"
    cp ${hosts_file} ${hosts_file}_vora
    cp ${hosts_file}_hdp ${hosts_file}
    k8s_master_host=`awk '/\[masters\]/ { getline; print $1}' ${hosts_file}_vora`
    echo "[kubemaster]" >> ${hosts_file}
    echo ${k8s_master_host} >> ${hosts_file}
    if [ ${1} == "CCLOUD" ];then
      echo "[kubemaster:vars]" >> ${hosts_file}
      echo "ansible_user=ccloud" >> ${hosts_file}
      echo "ansible_become=True" >> ${hosts_file}
      echo "ansible_become_user=root" >> ${hosts_file}
      echo "ansible_become_method=sudo" >> ${hosts_file}
      echo "ansible_become_ask_pass=False" >> ${hosts_file}
    fi
    INSTALL_VORA_SPARK_EXT="true"
    INSTALL_BDH_ADAPTER="true"
    deploy_vor_spark_ext "${@}"
    deploy_bdh_adapter "${@}"
    cp ${hosts_file} ${hosts_file}_hdp
  fi

}

function deploy_cluster_token(){
  # this also skip destroying the cluster if deploy token failed, user still can use the k8s cluster
  if ( ! bootstrap_cluster_on_demand "ansible-playbook -i ${hosts_file} ${ROOT_DIR}/playbooks/cloud/cluster-add-token.yml" ); then
    echo "\nDeploy cluster token failed!" >> ${WORKSPACE}/${BUILD_NUMBER}/result
  fi
}
