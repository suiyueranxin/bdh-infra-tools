#!/usr/bin/env bash
set -x
ROOT_DIR="/project"
env_file="/infrabox/output/env.sh"
source /infrabox/context/hera/common/common.sh

if [[ $VORA_VERSION ]]; then
  pushd ${ROOT_DIR}
    repo="ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack"
    clone_repo $repo
    pushd ${ROOT_DIR}/hanalite-releasepack
      VORA_VERSION_TAG=$(git tag | grep $VORA_VERSION | grep "rel")
      if [ $VORA_VERSION_TAG ]; then
        git checkout -b e2e-push $VORA_VERSION_TAG
        echo "## VORA_VERSION_TAG: ${VORA_VERSION_TAG}"
        cp ${ROOT_DIR}/get_component_version.py .
        chmod +x get_component_version.py
        VSYSTEM_VERSION=$(python get_component_version.py pom.xml hldep.hl-vsystem.version)
        VSOLUTION_VERSION=$(python get_component_version.py pom.xml hldep.hl-vsolution.version)
        APP_BASE_VERSION=$(python get_component_version.py pom.xml hldep.datahub-app-base.version)
        FLOWAGENT_VERSION=$(python get_component_version.py pom.xml hldep.datahub-flowagent.version)
        LICENSE_MANAGER_VERSION=$(python get_component_version.py pom.xml hldep.datahub-license-manager.version)
      fi
    popd
    git clone git@github.wdf.sap.corp:velocity/vsolution.git
    pushd ${ROOT_DIR}/vsolution
      VSOLUTION_TAG=$(git tag |grep $VSOLUTION_VERSION |grep "rel")
      if [ $VSOLUTION_TAG ]; then
        echo "##VSOLUTION_TAG = $VSOLUTION_TAG"
        git checkout -b e2e-push $VSOLUTION_TAG
        VFLOW_VERSION=$(cat deps/vflow.dep | grep VERSION| cut -d '"' -f4)
      fi
    popd
  popd
fi

echo "export VSYSTEM_VERSION=$VSYSTEM_VERSION" >> ${env_file}
echo "export VFLOW_VERSION=$VFLOW_VERSION" >> ${env_file}
echo "export VSOLUTION_VERSION=$VSOLUTION_VERSION" >> ${env_file}
echo "export APP_BASE_VERSION=$APP_BASE_VERSION" >> ${env_file}
echo "export FLOWAGENT_VERSION=$FLOWAGENT_VERSION" >> ${env_file}
echo "export LICENSE_MANAGER_VERSION=$LICENSE_MANAGER_VERSION" >> ${env_file}

cat ${env_file}
