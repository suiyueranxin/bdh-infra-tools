#!/bin/bash
set -ex

source /project/common.sh
TEST_SCRIPT_FOLDER="src/test/installer-test"

extract_installer(){
  export VORA_PACKAGE=$(find /infrabox/inputs -mindepth 2 -maxdepth 2 -name \*Foundation.tar.gz)
  if ! [ -f "$VORA_PACKAGE" ]; then
    echo "could not find Foundation.tar.gz from /infrabox/inputsi. Try downloading by ${VORA_VERSION}"
    if [[ ! ${VORA_VERSION} ]] || [[ ! ${VORA_KUBE_PREFIX_URL} ]]; then
      echo "VORA_VERSION or VORA_KUBE_PREFIX_URL is NULL. Can not download the DH package"
      exit 1
    fi
    DOWNLOAD_URL="${VORA_KUBE_PREFIX_URL}/${VORA_VERSION}/SAPDataHub-${VORA_VERSION}-Foundation.tar.gz"
    wget ${DOWNLOAD_URL} -P /project/
    export VORA_PACKAGE=$(ls -d /project/*Foundation.tar.gz)
  fi
  mkdir /installer && tar -zxf ${VORA_PACKAGE} -C /installer
}
 
echo "## extract installer package"
extract_installer

export PRODUCT_DIR=$(ls -d /installer/*Foundation)
echo "clone hanalite-releasepack"
pushd /project
  clone_hanalite_releasepack
  pushd /project/hanalite-releasepack/${TEST_SCRIPT_FOLDER}
    echo "## run test script"
    ./test.sh
    if [ $? == 0 ];then
      echo "## run test SUCCEED!"
      rm -rf ${PRODUCT_DIR} /project/*Foundation.tar.gz
    else
      echo "## run test FAILED!"
      rm -rf ${PRODUCT_DIR} /project/*Foundation.tar.gz
      exit 1
    fi
  popd
popd
exit 0
