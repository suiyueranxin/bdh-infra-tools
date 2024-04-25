#!/bin/bash
set -ex

mirror_image_on_prem() {
  echo "## Get Image list"
  mkdir -p /tmp/pkg
  pushd /tmp/pkg
  export PACKAGE_PATTERN=Foundation
  if [[ -n ${VORA_KUBE_SUFFIX} ]]; then
    PACKAGE_PATTERN=${VORA_KUBE_SUFFIX}
  fi
  echo "## VORA_VERSION: ${VORA_VERSION}"
  if [[ -z "${VORA_PACKAGE}" ]]; then
    curl -LO ${VORA_KUBE_PREFIX_URL}/${VORA_VERSION}/SAPDataHub-${VORA_VERSION}-${PACKAGE_PATTERN}.tar.gz
    export VORA_PACKAGE=$(ls -d /tmp/pkg/*${PACKAGE_PATTERN}.tar.gz)
  fi
  tar -zxf ${VORA_PACKAGE} -C /tmp/pkg
  export PRODUCT_DIR=$(ls -d /tmp/pkg/*${PACKAGE_PATTERN})
  ${PRODUCT_DIR}/install.sh -lt > /tmp/image_list
  popd

  echo "## image list"
  cat /tmp/image_list

  echo "## generator"
  export K8S_CLUSTER_NAME=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt)
  ${ROOT_DIR}/tools/generate_image_names.py < /tmp/image_list on_prem

  echo "## pull & push list"
  cat /tmp/pull_push_list

  echo "## pull and push images"
  ${ROOT_DIR}/tools/pull_and_push_docker_image.sh "on_prem"

  # For on premise case, false positive, missing images will be mirrored by installer.
  if [ $? != 0 ]; then
    echo "## Docker images mirror fail!"
    exit 0
  fi

  echo "## Docker images mirror success!"
}

mirror_image_on_cloud() {
  echo "## DH_VERSION: ${DH_VERSION}"
  sed -i "s/\${DH_VERSION}/${DH_VERSION}/g" project/image_list

  echo "## image list"
  cat project/image_list

  echo "## generator"

  /project/dhaas_mirror.py < project/image_list on_cloud

  echo "## pull and push images"
  /project/pull_and_push_docker_image.sh "on_cloud"

  if [ $? != 0 ]; then
    echo "## Docker images mirror fail!"
    exit 1
  fi

  echo "## Docker images mirror success!"
}

if [[ "${1}" == "on_cloud" ]]; then
  mirror_image_on_cloud
else
  mirror_image_on_prem
fi
