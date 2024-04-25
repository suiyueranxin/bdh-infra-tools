#!/bin/bash

set -ex

BASE_FOLDER=$(dirname $0)
echo ${BASE_FOLDER}

#python ${BASE_FOLDER}/../utils/check_service_status.py

if ! [ -x "$(command -v infrabox)" ]; then
  yum install -y python-pip
  yum install -y python-wheel
  python -m pip install --upgrade pip setuptools wheel
  pip install infraboxcli
fi

source ${BASE_FOLDER}/infrabox_stable_debug_env.sh
source ${BASE_FOLDER}/../utils/get_latest_commit_id.sh

source ${BASE_FOLDER}/infrabox_stable_debug_custom_commit_id.sh
if [ -z ${COMMIT_ID_STABLE} ]; then
get_latest_commit_id
fi

echo ${COMMIT_ID_STABLE}

if ! [ -f $INFRABOX_CA_BUNDLE ]; then
  mkdir -p $(dirname $INFRABOX_CA_BUNDLE)
  cp ${BASE_FOLDER}/ca.crt $INFRABOX_CA_BUNDLE
fi

if [ -d /tmp/hanalite-releasepack_continues_validation_stable_debug ]; then
  rm -rf /tmp/hanalite-releasepack_continues_validation_stable_debug/*
else
  mkdir -p /tmp/hanalite-releasepack_continues_validation_stable_debug
fi

pushd /tmp/hanalite-releasepack_continues_validation_stable_debug
cp ${BASE_FOLDER}/infrabox_stable_debug.json infrabox.json
sed -i "s/\"commit\": \"stable\",/\"commit\": \"${COMMIT_ID_STABLE}\",/g" infrabox.json
infrabox push
popd

rm -rf /tmp/hanalite-releasepack_continues_validation_stable_debug

