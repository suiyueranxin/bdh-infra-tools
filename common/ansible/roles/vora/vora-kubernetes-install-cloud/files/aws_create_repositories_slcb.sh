SLCB_PATH=$1
DOCKER_ARTIFACTORY=$2
PRODUCT_IMAGE=$3
IMAGE_TAG=$4
REGISTRY_SUFFIX=$5

SLCB_COPY_COMMAND="${SLCB_PATH}/slcb copy --ui_mode none -i ${SLCB_PATH}/inifile --SAP_PV_DOCKER_REPO ${DOCKER_ARTIFACTORY} --useBridgeImage ${PRODUCT_IMAGE}:${IMAGE_TAG} --listImages"

if [[ -z "${REGISTRY_SUFFIX}" ]]; then
  eval "$(${SLCB_COPY_COMMAND} | awk '{print "aws ecr create-repository --repository-name="$3}')"
else
  eval "$(${SLCB_COPY_COMMAND} | awk '{print "aws ecr create-repository --repository-name=${REGISTRY_SUFFIX}/"$3}')"
fi
