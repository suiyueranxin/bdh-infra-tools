#!/usr/bin/env bash

set -exo pipefail

clone_repo() {
  repo=${1:-"ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack"}
  clone_cmd="git clone "${repo}

  git config --global http.sslVerify "false"
  if [[ ${GERRIT_CHANGE_BRANCH} ]]; then
    clone_cmd=${clone_cmd}" --single-branch -b ${GERRIT_CHANGE_BRANCH}"
  else
    clone_cmd=${clone_cmd}" --no-single-branch"
  fi
  GIT_CLONE_DEPTH=100
  clone_cmd=${clone_cmd}" --depth=${GIT_CLONE_DEPTH}"

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

# get the version from pom.xml and insert into env.sh
# this function assume to run in the hanalite-releasepack folder
# get_component_version.py and list_component_versions.py must be in the /project folder
get_component_version_from_pom() {
  if [[ ! -f get_component_version.py ]] || [[ ! -f list_component_versions.py ]]; then
    cp /project/get_component_version.py ./
    cp /project/list_component_versions.py ./
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

  ALL_COMPONENTS_VERSIONS=$(python list_component_versions.py pom.xml)
  echo "export ALL_COMPONENTS_VERSIONS='$ALL_COMPONENTS_VERSIONS'" >> /env.sh
  echo "export VSYSTEM_VERSION=$VSYSTEM_VERSION" >> /env.sh
  echo "export APP_BASE_VERSION=$APP_BASE_VERSION" >> /env.sh
  echo "export APP_DATA_VERSION=$APP_DATA_VERSION" >> /env.sh
  echo "export FLOWAGENT_VERSION=$FLOWAGENT_VERSION" >> /env.sh
  echo "export LICENSE_MANAGER_VERSION=$LICENSE_MANAGER_VERSION" >> /env.sh
  echo "export HANALITE_LIB_VERSION=$HANALITE_LIB_VERSION" >> /env.sh
  echo "export SECURITY_OPERATOR_VERSION=$SECURITY_OPERATOR_VERSION" >> /env.sh
  echo "export SAPJVM_VERSION=$SAPJVM_VERSION" >> /env.sh
  echo "export DATA_TOOLS_UI_VERSION=$DATA_TOOLS_UI_VERSION" >> /env.sh
  echo "export SPARK_DATASOURCES_VERSION=$SPARK_DATASOURCES_VERSION" >> /env.sh
  echo "export VSYSTEM_UI_VERSION=$VSYSTEM_UI_VERSION" >> /env.sh
  echo "export UI_COMPONENTS_VERSION=$UI_COMPONENTS_VERSION" >> /env.sh
  echo "export VORA_TOOLS_VERSION=$VORA_TOOLS_VERSION" >> /env.sh
  echo "export CONSUL_VERSION=$CONSUL_VERSION" >> /env.sh
  echo "export HANA_REPLICATION_VERSION=$HANA_REPLICATION_VERSION" >> /env.sh
  echo "export DSP_RELEASE_VERSION=$DSP_RELEASE_VERSION" >> /env.sh
  echo "export DIAGNOSTICS_VERSION=$DIAGNOSTICS_VERSION" >> /env.sh
  echo "export STORAGEGATEWAY_VERSION=$STORAGEGATEWAY_VERSION" >> /env.sh
  chmod +x /env.sh

  VSOLUTION_VERSION=$(python get_component_version.py pom.xml hldep.hl-vsolution.version)
  VFLOW_VERSION=$(python get_component_version.py pom.xml hldep.hl-vflow.version)

  clone_repo "git@github.wdf.sap.corp:velocity/vsolution.git"
  pushd vsolution
    if [[ "${CURRENT_COMPONENT}" == "vsolution" ]]; then
      checkout_component_by_pr "vsolution"
    else
      VSOLUTION_TAG=$(git tag |grep $VSOLUTION_VERSION |grep "rel")
      if [ $VSOLUTION_TAG ]; then
        echo "##VSOLUTION_TAG = $VSOLUTION_TAG"
        git checkout -b e2e-push $VSOLUTION_TAG
      fi
    fi
    if [ -z "${VFLOW_VERSION}" ]; then
      if [ -f "deps/vflow.dep" ]; then
         VFLOW_VERSION=$(cat deps/vflow.dep | grep VERSION| cut -d '"' -f4)
      else
          VFLOW_VERSION=""
      fi
    fi
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

  echo "export DQ_INTEGRATION_VERSION=$DQ_INTEGRATION_VERSION" >> /env.sh
  echo "export VFLOW_SUB_ABAP_VERSION=$VFLOW_SUB_ABAP_VERSION" >> /env.sh
  echo "export VFLOW_VERSION=$VFLOW_VERSION" >> /env.sh
  echo "export VSOLUTION_VERSION=$VSOLUTION_VERSION" >> /env.sh
}

get_latest_full_product_yaml() {
  pushd /component-repo
    if [ -z "${CODE_LINE}" ]; then
      BRANCH="$(cat .git/HEAD | cut -b 17-)"
    else
      BRANCH=${CODE_LINE}
    fi
  popd

  if [ -d /hanalite-releasepack ]; then
    rm -rf /hanalite-releasepack
  else
    mkdir -p /hanalite-releasepack
  fi
  pushd /
    # set releasepack branch as the same branch with vsystem, set to master if there is no same branch
    branch_exists=`git ls-remote --heads ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack.git ${BRANCH} | wc -l`
    if [ -z "${CODE_TAG}" ]; then
      if [ $branch_exists -eq 0 ]; then
        code_tag="master"
      else
        code_tag=${BRANCH} 
      fi
    else
      code_tag=${CODE_TAG}
    fi
    echo "code_tag=${code_tag}"
    clone_repo "ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack"
    pushd /hanalite-releasepack
      git checkout ${code_tag}
      CFG_VERSION="$(cat cfg/VERSION)"
      #get the branch image version
      BRANCH_VERSION=$(python /project/get_branch_version.py ${BRANCH} ${CFG_VERSION} 2>&1)
      if [[ $BRANCH_VERSION =~ "branch_version=" ]]; then
        RELEASEPACK_VERSION=${BRANCH_VERSION#*branch_version=}
        echo "export RELEASEPACK_VERSION=$RELEASEPACK_VERSION" >> /env.sh
      fi
    popd
  popd

  if [ -z "$RELEASEPACK_VERSION" ]; then
    echo "Get latest releasepack version failed"
    exit 1
  fi
  export FULL_PRODUCT_YAML_TAG=$RELEASEPACK_VERSION
  if [[ "${BRANCH}" == "master" ]]; then
      export FULL_PRODUCT_YAML_TAG=${FULL_PRODUCT_YAML_TAG}
  fi

  pushd /tmp
    python /project/docker_pull.py "public.int.repositories.cloud.sap/com.sap.datahub.linuxx86_64/${1}:${FULL_PRODUCT_YAML_TAG}"
    tar -xf *.tar && rm -f *.tar
    find . -name layer.tar -exec tar -xf {} \;
    cp product/stack.yaml /stack.yaml
    rm -rf /tmp/*
  popd

}

# main
if [ -z "${PRODUCT_TYPE}" ]; then
    product_type=di-platform-full-product-bridge
else
    product_type=${PRODUCT_TYPE}
fi
get_latest_full_product_yaml $product_type
pushd /hanalite-releasepack
  git rev-parse --abbrev-ref HEAD
  echo "## get all component version from releasepack ${RELEASEPACK_VERSION}"
  get_component_version_from_pom
  cp images/com.sap.datahub.linuxx86_64/installer/src/bridges/${product_type}/bridge-profile.yaml /bridge-profile.yaml
popd
rm -rf /hanalite-releasepack
