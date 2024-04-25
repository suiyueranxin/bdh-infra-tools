#!/bin/bash
set -x
source /project/common.sh
echo "## start building..."
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

cp /project/settings.xml /usr/share/maven/conf
POM_FILE="/project/hanalite-releasepack/pom.xml"

mvn_build()
{
  pushd /project/hanalite-releasepack
    LOOP=1
    MAX_RETRY=3
    while [ ${LOOP} -le ${MAX_RETRY} ]
    do
      2>&1 mvn clean package > /infrabox/upload/archive/vorabuild.log
      if [ $? == 0 ];then
        break
      fi
      LOOP=$(( $LOOP + 1 ))
    done
    if [ ${LOOP} -gt ${MAX_RETRY} ];then
        cp /infrabox/upload/archive/vorabuild.log /infrabox/output/vorabuild.log
        die "vora build failed!"
    fi
    cp /infrabox/upload/archive/vorabuild.log /infrabox/output/vorabuild.log

    ls -alh /project/localDeployment/com.sap.datahub/SAPDataHub/*/*.tar.gz
    VORA_PACKAGE=$(ls /project/localDeployment/com.sap.datahub/SAPDataHub/*/SAPDataHub-*-DI-Assembly.tar.gz)
    VORA_VERSION=$(echo ${VORA_PACKAGE##*/} | awk -F - '{print $2}')
  popd
}

bridge_build()
{
  set -e
  pushd /project
    add_wdf_cer
    #if [[ -z ${SLCB_VERSION} ]]; then
    #  SLCB_VERSION='1.1.38'
    #fi
    # the ansible code for 1.1.38, 1.1.40, 1.1.42 are not compatible
    # so use fix version with code to avoid compatible in push validation
    if [[ "${USE_CUSTOMIZED_SLCB_BINARY}" == "true" ]] && [[ -n "${CUSOTOMIZED_SLCB_TAG}" ]]; then
      export SLCB_VERSION=${CUSOTOMIZED_SLCB_TAG}
    else
      install_file="/project/hanalite-releasepack/images/com.sap.datahub.linuxx86_64/installer/Dockerfile"
      LATEST_SLCB_VERSION=$(grep -E 'ARG SLC_BRIDGE_BASE_VERSION' ${install_file} |tr -d '[ARG SLC_BRIDGE_BASE_VERSION=]')
      export SLCB_VERSION=${LATEST_SLCB_VERSION}
    fi
       
    # get version from cfg/VERSION
    # this version won't have any -ms suffix
    VORA_VERSION=$(cat hanalite-releasepack/cfg/VERSION)
    if [[ -z "${VORA_VERSION}" ]]; then
      die "releasepack version is empty!"
    fi
    
    # get the image list
    # There are two different naming convention of image tag on premise and on cloud.
    # on premise: build_${INFRABOX_BUILD_NUMBER}   on cloud: ${VORA_VERSION}-${INFRABOX_BUILD_NUMBER}
    REPO="di-dev-cicd-v2.int.repositories.cloud.sap/infrabox/hanalite-releasepack"
    IMAGE="com.sap.datahub.linuxx86_64/di-releasepack-installer"
    TAG="build_${INFRABOX_BUILD_NUMBER}"
    CMD="image list -s /stack/self-contained.yaml"
    LIST_FILE="/project/image_from_releasepack_installer.txt"
    IMAGE_LIST_FILE="/infrabox/output/slcb_image_list.txt"
    docker run ${REPO}/${IMAGE}:${TAG} ${CMD} | sort | uniq > ${LIST_FILE}
    cat ${LIST_FILE}
    TARGET_REPO="di-dev-cicd-v2.int.repositories.cloud.sap/infrabox/hanalite-releasepack"
    python get_image_list.py ${LIST_FILE} ${IMAGE_LIST_FILE} ${SLCB_VERSION} ${TARGET_REPO}
    cp ${IMAGE_LIST_FILE} "/infrabox/upload/archive/slcb_image_list.txt"
    cat ${IMAGE_LIST_FILE}

  popd
  set +e
}

pushd /project
  clone_hanalite_releasepack
  pushd /project/hanalite-releasepack
    if [ -z "$GERRIT_CHANGE_BRANCH" ]; then
      GERRIT_CHANGE_BRANCH=$(git branch | grep \* | cut -d ' ' -f2 | cut -d '(' -f2)
    fi

    if [[ "$USE_FOR" == "NIGHTLY_VALIDATION" ]]; then
      git log --after="$(date -d '1 day ago' '+%Y-%m-%d %H:%M:%S')" --before="$(date '+%Y-%m-%d %H:%M:%S')" > /infrabox/output/recent_commit_log
      git log --after="$(date -d '1 day ago' '+%Y-%m-%d %H:%M:%S')" --before="$(date '+%Y-%m-%d %H:%M:%S')" --pretty=format:'{%n  "commit": "%H",%n  "author": "%aN <%aE>",%n  "date": "%ad",%n  "message": "%f"%n},' $@ | perl -pe 'BEGIN{print "["}; END{print "]\n"}' | perl -pe 's/},]/}]/' > /infrabox/output/recent_commit_log.json
    else
      git log -10 --date-order > /infrabox/output/recent_commit_log
      git log -10 --date-order --pretty=format:'{%n  "commit": "%H",%n  "author": "%aN <%aE>",%n  "date": "%ad",%n  "message": "%f"%n},' $@ | perl -pe 'BEGIN{print "["}; END{print "]\n"}' | perl -pe 's/},]/}]/' > /infrabox/output/recent_commit_log.json
    fi
  popd
popd


cp ${POM_FILE} /infrabox/upload/archive/pom.xml
if [[ -n "${INSTALL_VIA_SLCB}" ]] && [[ "${INSTALL_VIA_SLCB}" == "true" ]]; then
  bridge_build
else
  mvn_build
fi
echo "export VORA_VERSION=$VORA_VERSION" >> /infrabox/output/env.sh
echo "export GERRIT_CHANGE_BRANCH=$GERRIT_CHANGE_BRANCH" >> /infrabox/output/env.sh
if [[ -n ${SLCB_VERSION} ]]; then
  echo "export SLCB_VERSION=$SLCB_VERSION" >> /infrabox/output/env.sh
fi
pushd /project/hanalite-releasepack
  get_component_version_from_pom
popd

if [[ "$FTPENABLE" == "TRUE" ]]; then
  if [[ -z "${VORA_NAMESPACE_PREFIX}" ]]; then
    TEST_VORA_NAMESPACE_PREFIX=vora
  else
    TEST_VORA_NAMESPACE_PREFIX=${VORA_NAMESPACE_PREFIX}
  fi
  K8S_INSTALLER_NAMESPACE="vora-${TEST_VORA_NAMESPACE_PREFIX}-${INFRABOX_BUILD_NUMBER}-${INFRABOX_BUILD_RESTART_COUNTER}"
  /infrabox/context/common/ftp_upload.sh ${FTPHOST} ${FTPUSER} ${FTPPASS} ${K8S_INSTALLER_NAMESPACE} "/project/localDeployment/com.sap.datahub/SAPDataHub//${VORA_VERSION}"
else 
  mv /project/localDeployment/com.sap.datahub/SAPDataHub/*/*Foundation.tar.gz /infrabox/output
  mv /project/localDeployment/com.sap.datahub/SAPDataHub/*/*DI-Assembly.tar.gz /infrabox/output
fi

rm -rf /project/hanalite-releasepack
rm -rf /project/localDeployment
echo "build done..."

echo "## copy /infrabox/context to /infrabox/output/context"
# we need to exclude .infrabox because this contains /infrabox/output
rm -rf /infrabox/output/context
mkdir /infrabox/output/context
cd /infrabox/context
tar cf - --exclude=.infrabox  . | tar xf - -C /infrabox/output/context/

