#!/bin/bash

set -x

copy_log() {
  if [ -d /infrabox/inputs/log_collection*$1 ]; then
    mkdir -p /infrabox/upload/archive/$1
    cp -r /infrabox/inputs/log_collection*$1/  /infrabox/upload/archive/$1/
  fi
  for job_name in /infrabox/inputs/* ; do
    if [[ $job_name = *$1 ]] && [ -d "$job_name/execution_log" ]; then
      mkdir -p /infrabox/upload/archive/$1
      cp -r $job_name/execution_log/* /infrabox/upload/archive/$1/
    fi
  done
}

get_pr_label() {
    label=''
    if [[ -n "${GITHUB_REPOSITORY_FULL_NAME}" ]] && [[ -n "${GITHUB_PULL_REQUEST_NUMBER}" ]]; then
        set +x
        pr_url=${GITHUB_BASE_URL}/api/v3/repos/${GITHUB_REPOSITORY_FULL_NAME}/pulls/${GITHUB_PULL_REQUEST_NUMBER}
        $(curl -XGET ${pr_url} -k -H 'content-type: application/json' -o label.json)
        set -x
        label_list=$(jq '.labels' label.json)
        if [[ "${label_list}" != "[]" ]]; then
            label_str=$(jq '.labels[].name' label.json)
            # replace empty with '-' between each component
            label_str1=$(echo ${label_str} | sed 's/ /-/g')
            # remove the \"
            label=$(echo ${label_str1} | sed 's/\"//g')
        fi
     fi
     echo ${label}
}

if [ -z "$MANUALLY_BUILD_NUMBER" ]; then
  source /infrabox/inputs/build_copy_files/env.sh
  # fix the missing VORA_MILESTONE_PATH in milestone validation when install job failed.
  if [[ "${VORA_KUBE_PREFIX_URL}" ]] && [[ "${VORA_VERSION}" ]]; then
    PACKAGE_PATTERN="Foundation"
    if [[ -n "${VORA_KUBE_SUFFIX}" ]]; then
      PACKAGE_PATTERN=${VORA_KUBE_SUFFIX}
    fi
    export VORA_MILESTONE_PATH="${VORA_KUBE_PREFIX_URL}/${VORA_VERSION}/SAPDataHub-${VORA_VERSION}-${PACKAGE_PATTERN}.tar.gz"
  fi

  if [ -n "${K8S_CREATION_JOB}" ]; then
    OLD_IFS="$IFS" 
    IFS="," 
    arr=(${K8S_CREATION_JOB}) 
    IFS="$OLD_IFS" 
    for creation_job in ${arr[@]} 
    do
      if [[ -f /infrabox/inputs/${creation_job}/bdh_base_version.sh ]]; then
        source /infrabox/inputs/${creation_job}/bdh_base_version.sh
      fi
      if [[ -f /infrabox/inputs/${creation_job}/k8s_cluster.txt ]]; then
        if [[ "${creation_job}" == dhaas* ]]; then
          cluster_name_item=$(echo $creation_job |rev |cut -d '_' -f2 |rev)_$(echo $creation_job |rev |cut -d '_' -f1 |rev):$(cat /infrabox/inputs/${creation_job}/k8s_cluster.txt)
        else
          cluster_name_item=$(echo $creation_job |rev |cut -d '_' -f1 |rev):$(cat /infrabox/inputs/${creation_job}/k8s_cluster.txt)
        fi
        if [ -n "${k8s_clusters}" ] && [ -n "${cluster_name_item}" ]; then
          k8s_clusters=${k8s_clusters},${cluster_name_item}
        else
          k8s_clusters=${cluster_name_item}
        fi
      fi
    done
    if [ -n "${k8s_clusters}" ]; then
      export K8S_CLUSTER_NAMES=${k8s_clusters}
    fi
  fi

  if [ -n "${PARENT_INSTALL_JOB}" ]; then
    OLD_IFS="$IFS" 
    IFS="," 
    arr=(${PARENT_INSTALL_JOB}) 
    IFS="$OLD_IFS" 
    for install_job in ${arr[@]} 
    do
      source /infrabox/inputs/${install_job}/env.sh
    done
  fi

  echo "## VORA VERSION: ${VORA_VERSION}"

  echo "## Recently git commits: "
  cat /infrabox/inputs/build_copy_files/recent_commit_log

  echo "## Current Job json content:"
  cat /infrabox/job.json

  echo "## Copy logs to archive.."
  declare -a arr=("on_premise" "gke" "kops" "aks" "gardener_aws" "eks" "dhaas_aws")

  for platform in "${arr[@]}"
  do
    copy_log $platform
  done

  cp /infrabox/inputs/build_copy_files/recent_commit_log /infrabox/upload/archive/
  cp /infrabox/inputs/build_copy_files/vorabuild.log /infrabox/upload/archive/
  if [[ -n ${DIS_VERSION} ]]; then
    touch /infrabox/upload/archive/DIS_VERSION_${DIS_VERSION} 
  else
    touch /infrabox/upload/archive/VORA_VERSION_${VORA_VERSION}
  fi
  echo "## ALL_COMPONENTS_VERSIONS: ${ALL_COMPONENTS_VERSIONS}"
fi
if [[ -n ${DIS_VERSION} ]]; then
   export K8S_ADM_CFG_PATH_OUTPUT="/infrabox/inputs/${PARENT_INSTALL_JOB}/shoot-kubeconfig.yaml"

   set +e
   # get the PR labels
   pr_labels=$(get_pr_label)
   if [ -n "${pr_labels}" ]; then
     # regex match if PR labels has '(digit)', labels in the PR validation like this: (componet_name([0-9]+.[0-9]+.[0-9]+))+
     label_match=$(echo $pr_labels | grep -Eo "\(\d+\.+\d*.*\d*\)")
   fi  
   if [ -z "${pr_labels}" ] || [ -z "${label_match}" ]; then
     echo "## Skip send job report to Dashboard"
     exit 0
   fi
   set -e
else 
   export K8S_ADM_CFG_PATH_OUTPUT="/infrabox/inputs/${K8S_CREATION_JOB}/admin.conf"
fi

echo "## Send email notification.."
python send_notification.py

