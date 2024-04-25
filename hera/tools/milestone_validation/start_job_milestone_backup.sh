#!/bin/bash

set -ex

BASE_FOLDER=$(dirname $0)
echo ${BASE_FOLDER}
TARGET_VORA_VERSION=${1:-""}
TARGET_VORA_REPO_URL=${2:-""}
VORA_BRANCH=${3:-""}


source ${BASE_FOLDER}/infrabox_milestone_backup_env.sh

run_on_cloud="yes"
run_on_premise="yes"
if ! [ -f $INFRABOX_CA_BUNDLE ]; then
  mkdir -p $(dirname $INFRABOX_CA_BUNDLE)
  cp ${BASE_FOLDER}/ca.crt $INFRABOX_CA_BUNDLE
fi

if [ -d /tmp/hanalite-releasepack_continues_validation_backup ]; then
  rm -rf /tmp/hanalite-releasepack_continues_validation_backup/*
else
  mkdir -p /tmp/hanalite-releasepack_continues_validation_backup
fi

pushd /tmp/hanalite-releasepack_continues_validation_backup

if [ -z ${VORA_BRANCH} ]; then
  echo "No branch info specified, exit testing"
  exit 1
fi
if [[ "${VORA_BRANCH}" =~ ^"rel-3."* ]]; then
  run_on_cloud="no"
fi
if [[ "${VORA_BRANCH}" == "rel-dhaas" ]] || [[ "${VORA_BRANCH}" == "master" ]]; then
  run_on_premise="no"
fi
CHECKOUT_BRANCH=$VORA_BRANCH
if [[ "${VORA_BRANCH}" == "rel-"* ]]; then
    branch_prefix=$(echo $VORA_BRANCH |cut -d '-' -f2 |cut -d '.' -f1)
    if [ $branch_prefix -gt 2005 ]; then
      run_on_premise="no"
    fi
    branch_exists=`git ls-remote --heads git@github.wdf.sap.corp:bdh/bdh-infra-tools.git $VORA_BRANCH | wc -l`
    if [ $branch_exists -eq 0 ]; then
      CHECKOUT_BRANCH="master"
    fi
fi
TARGET_VORA_VERSION=${TARGET_VORA_VERSION//\"/} #strip "
VORA_KUBE_PREFIX_URL=${TARGET_VORA_REPO_URL//\"/} #strip "
VORA_KUBE_PREFIX_URL=${VORA_KUBE_PREFIX_URL//\//\\/}
infrabox_output="infrabox.json"
echo "{\"version\": 1, \"jobs\": [" > $infrabox_output
if [[ "${run_on_premise}" == "yes" ]]; then
  infraboxjson=$(cat ${BASE_FOLDER}/infrabox_milestone_backup.json)
  infraboxjson=${infraboxjson//DUMMY_DEPLOY_TYPE/on_premise}
  infraboxjson=${infraboxjson//DUMMY_REPLACE_VERSION/$TARGET_VORA_VERSION}
  infraboxjson=${infraboxjson//DUMMY_REPLACE_URL/$VORA_KUBE_PREFIX_URL}
  infraboxjson=${infraboxjson//DUMMY_REPLACE_BRANCH/$VORA_BRANCH}
  if [ -z ${BUBBLEUP_URL} ]; then
    echo "No BUBBLEUP_URL specified for ci dashboard registrtion......"
  else
    infraboxjson=${infraboxjson//BUBBLEUP_URL_DUMMY/$BUBBLEUP_URL}
  fi
  echo $infraboxjson >> $infrabox_output
fi
if [[ "${run_on_cloud}" == "yes" ]]; then
  if [[ "${run_on_premise}" == "yes" ]]; then
    echo "," >> $infrabox_output
  fi
  infraboxjson=$(cat ${BASE_FOLDER}/infrabox_milestone_backup.json)
  infraboxjson=${infraboxjson//DUMMY_DEPLOY_TYPE/on_cloud}
  infraboxjson=${infraboxjson//DUMMY_REPLACE_VERSION/$TARGET_VORA_VERSION}
  infraboxjson=${infraboxjson//DUMMY_REPLACE_URL/$VORA_KUBE_PREFIX_URL}
  infraboxjson=${infraboxjson//DUMMY_REPLACE_BRANCH/$VORA_BRANCH}
  if [ -z ${BUBBLEUP_URL} ]; then
    echo "No BUBBLEUP_URL specified for ci dashboard registrtion......"
  else
    infraboxjson=${infraboxjson//BUBBLEUP_URL_DUMMY/$BUBBLEUP_URL}
  fi
  echo $infraboxjson >> $infrabox_output
fi
echo "]}" >> $infrabox_output
cat $infrabox_output

# master and stable milestone validation will be run in same infrabox project
echo TARGET_VORA_VERSION = ${TARGET_VORA_VERSION}
source ${BASE_FOLDER}/../../common/common.sh
infrabox_push
popd

rm -rf /tmp/hanalite-releasepack_continues_validation_backup

