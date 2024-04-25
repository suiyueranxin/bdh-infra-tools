#!/bin/bash
set +e

APP_TEST=""
TENANT=""
USERNAME=""
SMOKE_TEST_PARAMS=""

while [[ $# -ge 1 ]]
do
key="$1"
case ${key} in
  --app-test=*)
  ARG="${key#*=}"
  if [ ! -z "$ARG" ]; then
    APP_TEST="$ARG"
  fi
  ;;
  --tenant=*)
  ARG="${key#*=}"
  if [ ! -z "$ARG" ]; then
    TENANT="$ARG"
  fi
  ;;
  --username=*)
  ARG="${key#*=}"
  if [ ! -z "$ARG" ]; then
    USERNAME="$ARG"
  fi
  ;;
  --skip-init ) SMOKE_TEST_PARAMS+="--skip-init " ;;
  --skip-docker-build ) SMOKE_TEST_PARAMS+="--skip-docker-build " ;;
esac
shift
done

if [ -z  "$VSYSTEM_HOST"  ]; then
  echo "### [level=error] Env variable VSYSTEM_HOST is not set"
  exit 1
fi

if [ -z  "$cloud_param"  ]; then
  echo "### [level=error] Env variable cloud_param is not set"
  exit 1
fi

if [ -z  "$VORA_PASSWORD"  ]; then
  echo "### [level=error] Env variable VORA_PASSWORD is not set"
  exit 1
fi

if [ -z  "$VORA_SYSTEM_TENANT_PASSWORD"  ]; then
  echo "### [level=error] Env variable VORA_SYSTEM_TENANT_PASSWORD is not set"
  exit 1
fi

SMOKE_TEST_PARAMS="--host $VSYSTEM_HOST $cloud_param --password $VORA_PASSWORD --systempassword $VORA_SYSTEM_TENANT_PASSWORD"

# no tests run by default
if [[ ${VALIDATION_TYPE} ]] && [[ ${VALIDATION_TYPE} == "SMOKE_CORE" ]]; then
    SMOKE_TEST_PARAMS+=" --smoke-core"
fi
if [[ ${VALIDATION_TYPE} ]] && [[ ${VALIDATION_TYPE} == "SMOKE_METADATA" ]]; then
    SMOKE_TEST_PARAMS+=" --smoke-metadata"
fi
if [[ ${VALIDATION_TYPE} ]] && [[ ${VALIDATION_TYPE} == "SCENARIO_VALIDATION" ]]; then
  SMOKE_TEST_PARAMS+=" --scenario"
fi
if [[ ${VALIDATION_TYPE} ]] && [[ ${VALIDATION_TYPE} == "MATS_CORE" ]]; then
  SMOKE_TEST_PARAMS+=" --mats-core"
fi
if [[ ${VALIDATION_TYPE} ]] && [[ ${VALIDATION_TYPE} == "MATS_METADATA" ]]; then
  SMOKE_TEST_PARAMS+=" --mats-metadata"
fi
if [[ ${VALIDATION_TYPE} ]] && [[ ${VALIDATION_TYPE} == "WEEKLY_E2E" ]]; then
  SMOKE_TEST_PARAMS+=" --customer --weekly-e2e"
fi

if [[ ${UPGRADE_TEST} ]]; then
  if [[ ${UPGRADE_TEST} == "PREPARATION" ]]; then
    SMOKE_TEST_PARAMS+=" --pre-upgrade"
  elif [[ ${UPGRADE_TEST} == "VALIDATION" ]]; then
    SMOKE_TEST_PARAMS+=" --post-upgrade --skip-init"
  else
    SMOKE_TEST_PARAMS+=" --upgrade-teardown"
  fi
fi

if [[ ${APP_TEST} ]]; then
  SMOKE_TEST_PARAMS+=" --tests ${APP_TEST}"
fi

if [[ ${TENANT} ]]; then
  SMOKE_TEST_PARAMS+=" --tenant ${TENANT}"
fi

if [[ ${USERNAME} ]]; then
  SMOKE_TEST_PARAMS+=" --usename ${USERNAME}"
fi

node index.js $SMOKE_TEST_PARAMS
app_test_result=$?

cp reports/* /infrabox/upload/testresult/
popd

kill $PORT_FORWARD_PID
wait $PORT_FORWARD_PID 2>/dev/null

if [ $app_test_result -ne 0 ] ; then
  echo "apps test Fails"
  echo "test suite failure number is: " $app_test_result
  exit 1
fi

echo "apps test done..."
