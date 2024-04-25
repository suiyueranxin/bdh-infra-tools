#!/bin/bash
set -ex

export ODTEM_BASE_URL=https://odtem-api.datahub.only.sap/api/v1
export BASE_URL=https://api.dashboard.datahub.only.sap:30711

PLAN_DEV_MASTER="{ \"GKE\": \"hanalite-releasepack_nightly_validation_nightly_dev_master_gke_plan\" }"
PLAN_DEV_STABLE="{ \"GKE\": \"hanalite_releasepack_night_dev_gke\", \"AWS-EKS\": \"hanalite_releasepack_night_dev_eks\", \"GARDENER-AWS\": \"hanalite_releasepack_night_dev_gardener_aws\", \"AZURE-AKS\": \"hanalite_releasepack_night_dev_aks\" }"
PLAN_FORMAL_MASTER="{ \"GKE\": \"hanalite-releasepack_nightly_validation_gke_plan\", \"AWS-EKS\": \"hanalite-releasepack_nightly_validation_eks_plan\", \"GARDENER-AWS\": \"hanalite-releasepack_nightly_validation_gardener_aws_plan\" }"
PLAN_FORMAL_STABLE="{ \"GKE\": \"hanalite-releasepack_nightly_validation_stable_gke_plan\", \"AWS-EKS\": \"hanalite-releasepack_nightly_validation_eks_plan\", \"GARDENER-AWS\": \"hanalite-releasepack_nightly_validation_stable_gardner_aws_plan\" }"
PLAN_MILESTONE_MASTER="{ \"GKE\": \"milestone_master_test_plan\" }"
PLAN_MILESTONE_STABLE="{ \"GKE\": \"milestone_stable_test_plan\" }"

INFRABOX_JSON_DEV_MASTER=infrabox_debug_gke.json
INFRABOX_JSON_DEV_STABLE=infrabox_stable_debug.json
INFRABOX_JSON_FORMAL_MASTER=infrabox.json
INFRABOX_JSON_FORMAL_STABLE=infrabox_stable.json

DEV_OR_FORMAL=${1}
VALIDATION_BRANCH=${2}
if [ ! $DEV_OR_FORMAL ];then
    echo "Usage: \
          Run developing nightly with option: <DEV or FORMAL> <MASTER or STABLE>"
    exit 1
fi
echo $DEV_OR_FORMAL

BASE_FOLDER=$(dirname $0)
echo ${BASE_FOLDER}

#python ${BASE_FOLDER}/../utils/check_service_status.py 

if ! [ -x "$(command -v infrabox)" ]; then
  yum install -y python-pip
  yum install -y python-wheel
  python -m pip install --upgrade pip setuptools wheel
  pip install infraboxcli
fi

# FORMAL NIGHTLY MASTER
if [[ "${DEV_OR_FORMAL}" == "FORMAL" ]] && [[ "${VALIDATION_BRANCH}" == "MASTER" ]]; then
  source ${BASE_FOLDER}/infrabox_env.sh
fi 
# FORMAL NIGHTLY STABLE
if [[ "${DEV_OR_FORMAL}" == "FORMAL" ]] && [[ "${VALIDATION_BRANCH}" == "STABLE" ]]; then
  source ${BASE_FOLDER}/infrabox_stable_env.sh
fi
# DEV NIGHTLY MASTER
if [[ "${DEV_OR_FORMAL}" == "DEV" ]] && [[ "${VALIDATION_BRANCH}" == "MASTER" ]]; then
  source ${BASE_FOLDER}/infrabox_debug_gke_env.sh
fi
# DEV NIGHTLY STABLE
if [[ "${DEV_OR_FORMAL}" == "DEV" ]] && [[ "${VALIDATION_BRANCH}" == "STABLE" ]]; then
  source ${BASE_FOLDER}/infrabox_debug_env.sh
fi

if ! [ -f $INFRABOX_CA_BUNDLE ]; then
  mkdir -p $(dirname $INFRABOX_CA_BUNDLE)
  cp ${BASE_FOLDER}/ca.crt $INFRABOX_CA_BUNDLE
fi

if [ -d /tmp/hanalite-releasepack_continues_validation ]; then
  rm -rf /tmp/hanalite-releasepack_continues_validation/*
else
  mkdir -p /tmp/hanalite-releasepack_continues_validation
fi

# update the test plan
if [[ "${DEV_OR_FORMAL}" == "FORMAL" ]];then
  if [[ "${VALIDATION_BRANCH}" == "MASTER" ]]; then
     export DEV_TEST_PLAN_NAME=${PLAN_DEV_MASTER}
     export FORMAL_TEST_PLAN_NAME=${PLAN_FORMAL_MASTER}
     export MILESTONE_TEST_PLAN_NAME=${PLAN_MILESTONE_MASTER}
     export CODE_BRANCH="master"
  else
     export DEV_TEST_PLAN_NAME=${PLAN_DEV_STABLE}
     export FORMAL_TEST_PLAN_NAME=${PLAN_FORMAL_STABLE}
     export MILESTONE_TEST_PLAN_NAME=${PLAN_MILESTONE_STABLE}
     export CODE_BRANCH="stable"
  fi
  python ${BASE_FOLDER}/update_test_plan.py
  echo "Update formal test plan $FORMAL_TEST_PLAN_NAME complete"
fi

mkdir -p /tmp/hanalite-releasepack_continues_validation
pushd /tmp/hanalite-releasepack_continues_validation
git clone ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack
pushd /tmp/hanalite-releasepack_continues_validation/hanalite-releasepack

if [[ "${DEV_OR_FORMAL}" == "DEV" ]];then
  if [[ "${VALIDATION_BRANCH}" == "MASTER" ]]; then
    SOURCE_JSON=${BASE_FOLDER}/${INFRABOX_JSON_DEV_MASTER}
  else
    SOURCE_JSON=${BASE_FOLDER}/${INFRABOX_JSON_DEV_STABLE}
  fi  
else
  if [[ "${VALIDATION_BRANCH}" == "MASTER" ]]; then
    SOURCE_JSON=${BASE_FOLDER}/${INFRABOX_JSON_FORMAL_MASTER}
  else
    git checkout stable
    SOURCE_JSON=${BASE_FOLDER}/${INFRABOX_JSON_FORMAL_STABLE}
  fi
fi

cp ${SOURCE_JSON} infrabox.json
infrabox push

popd
popd

rm -rf /tmp/hanalite-releasepack_continues_validation

