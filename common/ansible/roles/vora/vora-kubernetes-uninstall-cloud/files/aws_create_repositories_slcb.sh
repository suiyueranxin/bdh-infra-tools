SLCB_PATH=$1
DOCKER_ARTIFACTORY=$2
PRODUCT_IMAGE=$3
REGISTRY_SUFFIX=$4

SLCB_COPY_COMMAND="${SLCB_PATH}/slcb copy --ui_mode none --SAP_PV_DOCKER_REPO ${DOCKER_ARTIFACTORY} --useBridgeImage ${PRODUCT_IMAGE} --listImages"

if [[ -z "${REGISTRY_SUFFIX}" ]]; then
  eval "$(${SLCB_COPY_COMMAND} | awk '{print "aws ecr create-repository --repository-name="$1}')"
else
  eval "$(${SLCB_COPY_COMMAND} | awk '{print "aws ecr create-repository --repository-name=${REGISTRY_SUFFIX}/"$1}')"
fi

