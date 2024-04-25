#!/bin/bash

die() {
  output_str=$'ERROR: \n'
  >&2 echo "${output_str}$*"
  exit 1
}

clone_repo() {
  repo=${1:-"ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack"}
  clone_cmd="git clone "${repo}
  if [[ -z "${GIT_CLONE_DEPTH}" ]]; then
    GIT_CLONE_DEPTH=100
  fi
  git config --global http.sslVerify "false"
  branch=${2:-${GERRIT_CHANGE_BRANCH}}
  if [ -n "$branch" ]; then
    clone_cmd=${clone_cmd}" --single-branch -b ${branch}"
  else
    clone_cmd=${clone_cmd}" --no-single-branch"
  fi
  if [[ ${GIT_CLONE_DEPTH} > 0 ]]; then
    clone_cmd=${clone_cmd}" --depth=${GIT_CLONE_DEPTH}"
  fi
  RETRY=6
  for ((i = 1; i <= ${RETRY}; i++)); do
    ${clone_cmd}
    if [ $? -eq 0 ]; then
      break
    else
      repo_name=$(echo $repo | awk -F "/" '{print $NF}')
      rm -rf $repo_name
    fi
    if [[ $i == ${RETRY} ]]; then
      echo "clone $repo failed"
      return 1
    fi
    sleep 60
  done
  return 0
}

clone_hanalite_releasepack() {
  repo="ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack"
  clone_repo $repo
  if [ $? -ne 0 ]; then
    exit 1
  fi
  set -e
  if [[ $GERRIT_CHANGE_PROJECT ]] && [[ "$GERRIT_CHANGE_PROJECT" == "hanalite-releasepack" ]]; then
    pushd /project/hanalite-releasepack
      if [[ $GERRIT_CHANGE_BRANCH ]] && [[ "$GERRIT_CHANGE_BRANCH" != "master" ]]; then
        git checkout $GERRIT_CHANGE_BRANCH
      fi
      if [ $GERRIT_PATCHSET_REF ];then
        git fetch ${repo} $GERRIT_PATCHSET_REF && git checkout FETCH_HEAD
      fi
    popd
  fi
  set +e
}

# get the version from pom.xml and insert into env.sh
# this function assume to run in the hanalite-releasepack folder
# get_component_version.py and list_component_versions.py must be in the /project folder
get_component_version_from_pom() {
  set -e
  if [[ ! -f get_component_version.py ]] || [[ ! -f list_component_versions.py ]]; then
    cp /project/get_component_version.py ./
    chmod +x get_component_version.py
    cp /project/list_component_versions.py ./
    chmod +x list_component_versions.py
  fi
  VSYSTEM_VERSION=$(python get_component_version.py pom.xml hldep.hl-vsystem.version)
  APP_BASE_VERSION=$(python get_component_version.py pom.xml hldep.datahub-app-base.version)
  APP_DATA_VERSION=$(python get_component_version.py pom.xml hldep.datahub-app-data.version)
  FLOWAGENT_VERSION=$(python get_component_version.py pom.xml hldep.datahub-flowagent.version)
  LICENSE_MANAGER_VERSION=$(python get_component_version.py pom.xml hldep.datahub-license-manager.version)
  HANALITE_LIB_VERSION=$(python get_component_version.py pom.xml hldep.hl-lib.version)
  SECURITY_OPERATOR_VERSION=$(python get_component_version.py pom.xml hldep.security-operator.version)
  SAPJVM_VERSION=$(python get_component_version.py pom.xml hldep.sapjvm.version)
  DATA_TOOLS_UI_VERSION=$(python get_component_version.py pom.xml hldep.hl-data-tools-ui.version)
  SPARK_DATASOURCES_VERSION=$(python get_component_version.py pom.xml hldep.hl-spark-datasources.version)
  VSYSTEM_UI_VERSION=$(python get_component_version.py pom.xml hldep.hl-vsystem-ui.version)
  UI_COMPONENTS_VERSION=$(python get_component_version.py pom.xml hldep.hl-ui-components.version)
  VORA_TOOLS_VERSION=$(python get_component_version.py pom.xml hldep.hl-vora-tools.version)
  CONSUL_VERSION=$(python get_component_version.py pom.xml hldep.consul.version)
  HANA_REPLICATION_VERSION=$(python get_component_version.py pom.xml hldep.hl-hana-replication.version)
  DSP_RELEASE_VERSION=$(python get_component_version.py pom.xml hldep.dsp-release.version)
  DIAGNOSTICS_VERSION=$(python get_component_version.py pom.xml hldep.diagnostics.version)
  STORAGEGATEWAY_VERSION=$(python get_component_version.py pom.xml hldep.storagegateway.version)
  RMS_VERSION=$(python get_component_version.py pom.xml hldep.rms.version)
  CONNECTION_SERVICE_VERSION=$(python get_component_version.py pom.xml hldep.connection-service.version)
  VFLOW_VERSION=$(python get_component_version.py pom.xml hldep.hl-vflow.version)

  ALL_COMPONENTS_VERSIONS=$(python list_component_versions.py pom.xml)
  echo "export ALL_COMPONENTS_VERSIONS='$ALL_COMPONENTS_VERSIONS'" >> /infrabox/output/env.sh
  echo "export VSYSTEM_VERSION=$VSYSTEM_VERSION" >> /infrabox/output/env.sh
  echo "export APP_BASE_VERSION=$APP_BASE_VERSION" >> /infrabox/output/env.sh
  echo "export APP_DATA_VERSION=$APP_DATA_VERSION" >> /infrabox/output/env.sh
  echo "export FLOWAGENT_VERSION=$FLOWAGENT_VERSION" >> /infrabox/output/env.sh
  echo "export LICENSE_MANAGER_VERSION=$LICENSE_MANAGER_VERSION" >> /infrabox/output/env.sh
  echo "export HANALITE_LIB_VERSION=$HANALITE_LIB_VERSION" >> /infrabox/output/env.sh
  echo "export SECURITY_OPERATOR_VERSION=$SECURITY_OPERATOR_VERSION" >> /infrabox/output/env.sh
  echo "export SAPJVM_VERSION=$SAPJVM_VERSION" >> /infrabox/output/env.sh
  echo "export DATA_TOOLS_UI_VERSION=$DATA_TOOLS_UI_VERSION" >> /infrabox/output/env.sh
  echo "export SPARK_DATASOURCES_VERSION=$SPARK_DATASOURCES_VERSION" >> /infrabox/output/env.sh
  echo "export VSYSTEM_UI_VERSION=$VSYSTEM_UI_VERSION" >> /infrabox/output/env.sh
  echo "export UI_COMPONENTS_VERSION=$UI_COMPONENTS_VERSION" >> /infrabox/output/env.sh
  echo "export VORA_TOOLS_VERSION=$VORA_TOOLS_VERSION" >> /infrabox/output/env.sh
  echo "export CONSUL_VERSION=$CONSUL_VERSION" >> /infrabox/output/env.sh
  echo "export HANA_REPLICATION_VERSION=$HANA_REPLICATION_VERSION" >> /infrabox/output/env.sh
  echo "export DSP_RELEASE_VERSION=$DSP_RELEASE_VERSION" >> /infrabox/output/env.sh
  echo "export DIAGNOSTICS_VERSION=$DIAGNOSTICS_VERSION" >> /infrabox/output/env.sh
  echo "export STORAGEGATEWAY_VERSION=$STORAGEGATEWAY_VERSION" >> /infrabox/output/env.sh
  echo "export VFLOW_VERSION=$VFLOW_VERSION" >> /infrabox/output/env.sh
  
  if  [[ "$RMS_VERSION" = [0-9]*\.[0-9]*\.[0-9]* ]]; then echo "export RMS_VERSION=$RMS_VERSION" >> /infrabox/output/env.sh; fi
  if  [[ "$CONNECTION_SERVICE_VERSION" = [0-9]*\.[0-9]*\.[0-9]* ]]; then echo "export CONNECTION_SERVICE_VERSION=$CONNECTION_SERVICE_VERSION" >> /infrabox/output/env.sh; fi

  chmod +x /infrabox/output/env.sh

  VSOLUTION_VERSION=$(python get_component_version.py pom.xml hldep.hl-vsolution.version)
  clone_repo "git@github.wdf.sap.corp:velocity/vsolution.git"
  pushd vsolution
  if [[ "${CURRENT_COMPONENT}" == "vsolution" ]]; then
    checkout_component_by_pr "vsolution"
  else
    VSOLUTION_TAG=$(git tag |grep $VSOLUTION_VERSION |grep "rel")
    if [ $VSOLUTION_TAG ]; then
      echo "##VSOLUTION_TAG = $VSOLUTION_TAG"
      git checkout -b e2e-push $VSOLUTION_TAG
      if [ -z "${VFLOW_VERSION}" ]; then
        if [ -f "deps/vflow.dep" ]; then
          VFLOW_VERSION=$(cat deps/vflow.dep | grep VERSION| cut -d '"' -f4)
        else
          VFLOW_VERSION=""
        fi
      fi
      VFLOW_SUB_ABAP_VERSION=$(grep -A3 -m1 vsolution_vflow_sub_abap cfg/import.ais |grep version | awk '{print $2}' | cut -d \" -f 2)
    fi
  fi
  if [ -z "${VFLOW_VERSION}" ]; then
    if [ -f "deps/vflow.dep" ]; then
      VFLOW_VERSION=$(cat deps/vflow.dep | grep VERSION| cut -d '"' -f4)
    else
      VFLOW_VERSION=""
    fi
  fi
  VFLOW_SUB_ABAP_VERSION=$(grep -A3 -m1 vsolution_vflow_sub_abap cfg/import.ais |grep version | awk '{print $2}' | cut -d \" -f 2)
  popd

  clone_repo "git@github.wdf.sap.corp:bdh/datahub-flowagent.git"
  pushd datahub-flowagent
  FLOWAGENT_TAG=$(git tag |grep $FLOWAGENT_VERSION |grep "rel")
  if [ $FLOWAGENT_TAG ]; then
     echo "##FLOWAGENT_TAG= $FLOWAGENT_TAG"
     git checkout -b e2e-push $FLOWAGENT_TAG
     DQ_INTEGRATION_VERSION=$(python ../get_component_version.py build/parent/pom.xml hldep.datahub-dq-integration.version)
  fi
  popd

  echo "export DQ_INTEGRATION_VERSION=$DQ_INTEGRATION_VERSION" >> /infrabox/output/env.sh
  echo "export VFLOW_SUB_ABAP_VERSION=$VFLOW_SUB_ABAP_VERSION" >> /infrabox/output/env.sh
  echo "export VFLOW_VERSION=$VFLOW_VERSION" >> /infrabox/output/env.sh
  echo "export VSOLUTION_VERSION=$VSOLUTION_VERSION" >> /infrabox/output/env.sh
  set +e
}

# VSYSTEM_VERSION must be set. eg: VSYSTEM_VERSION=2.6.9
# Else, default VCTL version will be used 
download_vctl() {
  VCTL_FROM_INSTALLER="/infrabox/inputs/${PARENT_INSTALL_JOB}/vctl"
  if [ -f ${VCTL_FROM_INSTALLER} ]; then
    chmod +x ${VCTL_FROM_INSTALLER}
    cp ${VCTL_FROM_INSTALLER} /usr/local/bin/; cp ${VCTL_FROM_INSTALLER} ./
    echo "Use the vctl from ${PARENT_INSTALL_JOB}"
    return
  fi
  DEFAULT_VCTL_VERSION="2002.0.38"
    DOWNLOAD_URL_PREFIX="https://int.repositories.cloud.sap/artifactory/build-milestones/com/sap/hana/hl/linuxx86_64/vsystem-client"
  echo "Download vctl"
  RETRY=3
  VCTL_DOWNLOAD_LINK="${DOWNLOAD_URL_PREFIX}/${VSYSTEM_VERSION}/vsystem-client-${VSYSTEM_VERSION}-linuxx86_64.tar.gz"
  for ((i = 1; i <= ${RETRY}; i++)); do
    curl --output /dev/null --silent --head --fail -k ${VCTL_DOWNLOAD_LINK}
    if [ $? -ne 0 ]; then
      echo "## vctl version $VSYSTEM_VERSION not avaliable, fall back to default vctl version"
      VCTL_DOWNLOAD_LINK="${DOWNLOAD_URL_PREFIX}/${DEFAULT_VCTL_VERSION}/vsystem-client-${DEFAULT_VCTL_VERSION}-linuxx86_64.tar.gz"
    fi
    curl -Ok ${VCTL_DOWNLOAD_LINK}
    if [ $? -ne 0 ]; then
      if [[ $i < ${RETRY} ]]; then
        echo "Download vctl failed. Retry..."
        sleep 10s
        continue
      fi
      echo "## Warning! Download vctl failed!"
    else
      break
    fi
  done
  tar -xf vsystem-client-*-linuxx86_64.tar.gz
  if [ ! -f "./vctl" ];then
    echo "Extract vctl package failed!"
  fi
  chmod +x ./vctl
  cp ./vctl /usr/local/bin/
  rm -f vsystem-client-*-linuxx86_64.tar.gz
}

# get current job name from job.json, need jq
get_current_job_name() {
  CURRENT_JOB_NAME=$(jq -r .job.name /infrabox/job.json)
  CURRENT_JOB_NAME=${CURRENT_JOB_NAME##*/}
  CURRENT_JOB_NAME=$(echo ${CURRENT_JOB_NAME} | cut -d'.' -f1)
}

# checkout the component repo by pr
checkout_component_by_pr() {
  if [ $# -ne 1 ]; then
    echo "usage: checkout_component_by_pr component_name_checkout_for_test"
    return 1
  fi
  if [[ "${CURRENT_COMPONENT}" != ${1} ]]; then
    return 0
  fi
  if [[ ${GITHUB_PULL_REQUEST_NUMBER} ]] && [[ ${INFRABOX_GIT_BRANCH} ]]; then
    git fetch origin pull/${GITHUB_PULL_REQUEST_NUMBER}/head:${INFRABOX_GIT_BRANCH} && git checkout ${INFRABOX_GIT_BRANCH}
    if [ $? -ne 0 ]; then
      echo "## checkout compoent by PR branch $INFRABOX_GIT_BRANCH and ID $GITHUB_PULL_REQUEST_NUMBER failed!"
      return 1
    fi
  fi
  return 0
}

# port_forward $pod $port $type
# wait 5 minutes to check if the port is listening
# type should be service/pod/deployment
# WARNNING: this function will overwirte the $PID enviroment
# $NAMESPACE env must be set
port_forward() {
  obj=${1}
  port=${2}
  type=${3}
  RETRY=5
  for ((i = 1; i <= ${RETRY}; i++)); do
    kubectl --namespace=$NAMESPACE port-forward ${type}/${obj} ${port} &
    pid=$!
    sleep 2
    netstat -na |grep "127.0.0.1:${port}"  |grep LISTEN
    if [ $? -eq 0 ]; then
      break
    elif [ $i -eq ${RETRY} ]; then
      echo "### [level=error] port ${port} is not listening after ${RETRY} minutes."
      return 1
    else
      sleep 60
    fi
  done
  PID=$pid
  return 0
}
# input VORA_VERSION
# output e2e_branch
get_e2e_branch_by_ver() {
    VER=${1}
    E2E_GIT_BRANCH=""

    if [[ $VER =~ ^2\.5 ]]; then
        E2E_GIT_BRANCH="rel-2.5.1"
    elif [[ $VER =~ ^2\.6 ]]; then
        E2E_GIT_BRANCH="rel-2.6"
    elif [[ $VER =~ ^2\.7 ]]; then
        E2E_GIT_BRANCH="rel-2.7"
    elif [[ $VER =~ ^3\.0\. ]]; then
        E2E_GIT_BRANCH="rel-3.0.2"
    elif [[ $VER =~ ^3\.1\. ]]; then
        E2E_GIT_BRANCH="rel-3.1"
    elif [[ $VER =~ ^3\.2\. ]]; then
        E2E_GIT_BRANCH="rel-3.2"
    elif [[ $VER =~ ^3\.3\. ]]; then
        E2E_GIT_BRANCH="rel-3.3"
    elif [[ $VER =~ \.0$ ]]; then
        # new branch stratage, versions ends with 0 is from main branch
        E2E_GIT_BRANCH="main"
    else
        #keep this for old releases from main branch
        if [[ $(echo $VER |cut -d '-' -f2) == "ms" ]]; then
            E2E_GIT_BRANCH="main"
        else
          prefix=$(echo $VER |cut -d '.' -f1)
          branch_name="rel-"$prefix
          git config --global http.sslVerify false
          branch_exists=$(git ls-remote --heads git@github.wdf.sap.corp:bdh/datahub-e2e-test.git $branch_name | wc -l)
          if [ $branch_exists -eq 0 ]; then
            echo "E2E test branch ${branch_name} not exist, use main by default"
            E2E_GIT_BRANCH="main"
          else
            E2E_GIT_BRANCH=${branch_name}
          fi
        fi
    fi
}

infrabox_push() {
  set -e 
  RETRY=3
  for ((i = 1; i <= ${RETRY}; i++)); do
    infrabox push
    if [ $? -eq 0 ]; then
      break
    fi
    sleep 60
  done
  set +e
}

get_tag_by_version_and_branch() {
    VORA_VERSION=${1}
    GERRIT_CHANGE_BRANCH=${2}
    if [[ ${GERRIT_CHANGE_BRANCH} ]]; then
      if [[ "${GERRIT_CHANGE_BRANCH}" == "master" ]]; then
        VORA_VERSION_TAG=$(git tag --list ms/${VORA_VERSION}*)
      else
        # only release from master branch will have ms/, for all other branches, use rel instead.
        VORA_VERSION_TAG=$(git tag --list rel/${VORA_VERSION}*)
      fi
    else
      set +e
      # start from 3.0.x release, all milestone will have GERRIT_CHANGE_BRANCH in installer job
      # the code below is for backward compatible 
      # master branch will have *.0.*. string format e.g: 2002.0.15 or 2002.0.15-ms
      echo $VORA_VERSION |grep "[0-9]*\.0\..*"
      if [ $? -eq 0 ]; then
        VORA_VERSION_TAG=$(git tag --list ms/${VORA_VERSION}*)
      fi
      # for other branches, it may have both *.0.* or *.1.*, but the tag will lead with rel/
      if [[ -z "${VORA_VERSION_TAG}" ]]; then
        VORA_VERSION_TAG=$(git tag --list rel/${VORA_VERSION}*)
      fi
    fi
}

add_wdf_cer() {
    openssl s_client -connect public.int.repositories.cloud.sap -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM | tee /usr/local/share/ca-certificates/docker.wdf.sap.corp.crt
    openssl s_client -connect di-dev-cicd-docker.int.repositories.cloud.sap:443 -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM | tee /usr/local/share/ca-certificates/di-dev-cicd-docker.int.repositories.cloud.sap.crt
    openssl s_client -connect di-dev-cicd-v2.int.repositories.cloud.sap:443 -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM | tee /usr/local/share/ca-certificates/di-dev-cicd-v2.int.repositories.cloud.sap.crt
    update-ca-certificates
}

dump_k8s_describe() {
  if [[ -z "${NAMESPACE}" ]]; then
      DI_NAMESPACE=$(kubectl get ns | grep -v -e kube-public -e kube-system  -e default -e datahub-system | awk 'FNR == 2 {print $1}')
  else
      DI_NAMESPACE=${NAMESPACE}
  fi
  if [[ ! -d /tmp/pod_des_logs ]]; then
    mkdir -p /tmp/pod_des_logs
    chmod -R 777 /tmp/pod_des_logs 
  fi
  python /infrabox/context/common/ansible/roles/vora/vora-kubernetes-install/files/generate_pods_describe_log.py $DI_NAMESPACE /tmp/pod_des_logs

  tar -cvzf /infrabox/upload/archive/k8s_describe.tar.gz /tmp/pod_des_logs
}

dump_k8s_cluster_info() {
  if [[ -z "${NAMESPACE}" ]]; then
      DI_NAMESPACE=$(kubectl get ns | grep -v -e kube-public -e kube-system  -e default -e datahub-system | awk 'FNR == 2 {print $1}')
  else
      DI_NAMESPACE=${NAMESPACE}
  fi
  mkdir -p /tmp/dump_k8s
  kubectl cluster-info dump --output-directory=/tmp/dump_k8s/ --all-namespaces
  if [[ -n "$DI_NAMESPACE" ]]; then
      # get vsystem init container log
      mkdir -p /tmp/dump_k8s/${DI_NAMESPACE}
      VSYSTEM_INIT_CONTAINER="vsystem-hana-init"
      VSYSTEM_POD=$(kubectl get pods -l vora-component=vsystem -n ${DI_NAMESPACE} -o go-template --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')
      kubectl logs ${VSYSTEM_POD} -n ${DI_NAMESPACE} -c ${VSYSTEM_INIT_CONTAINER} > /tmp/dump_k8s/${DI_NAMESPACE}/${VSYSTEM_INIT_CONTAINER}.log
  fi
  tar -cvzf /infrabox/upload/archive/k8s_dump.tar.gz /tmp/dump_k8s

  if [[ -n "$INFRABOX_JOB_URL" ]]; then
      job_name=$(echo $INFRABOX_JOB_URL | awk -F "/" '{print $NF}')
      if [[ !($job_name =~ 'install') ]]; then
          dump_k8s_describe
      fi
  fi

}
