#!/bin/bash
set -x
if [ -n "${PARENT_INSTALL_JOB}" ]; then
  if [ ! -f /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh ]; then
    echo "/infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh does not exist. Skip the current job"
    exit 0
  else
    source /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh
  fi
else
  echo "## Skip sourcing env.sh, Using external env information..."
fi
source /project/common.sh

LOG_OUTPUT_DIR="/infrabox/output/execution_log/vsystem_e2e"
mkdir -p $LOG_OUTPUT_DIR

GIT_SSL_NO_VERIFY=1
export PATH=$PATH:$GOROOT/bin:$GOPATH/bin

echo "## Start vsystem test..."
pushd /go/src/github.wdf.sap.corp/velocity
  git config --global http.sslVerify false
  git clone git@github.wdf.sap.corp:velocity/vsystem.git
  pushd /go/src/github.wdf.sap.corp/velocity/vsystem
    git log -20 --date-order > /infrabox/upload/archive/recent_commit.log
    cp /infrabox/upload/archive/recent_commit.log ${LOG_OUTPUT_DIR}
    if [ $VSYSTEM_VERSION ]; then
      VSYSTEM_TAG=$(git tag |grep $VSYSTEM_VERSION |grep "rel")
      if [ $VSYSTEM_TAG ]; then
        echo "##VSYSTEM_TAG = $VSYSTEM_TAG"
        git checkout -b e2e-push $VSYSTEM_TAG
      fi
    fi
  popd
popd

if [[ ${PROVISION_PLATFORM} != "MONSOON" ]];then
  ADDRESS="$(echo ${VSYSTEM_ENDPOINT} | awk -F':' '{print $1":"$2}')/"
else
  ADDRESS=${VSYSTEM_ENDPOINT}
fi

if [[ "${E2E_TYPE}" == "e2e-test" ]];then
  if [ -d "/go/src/github.wdf.sap.corp/velocity/vsystem/tests/e2e-test" ];then
    pushd /go/src/github.wdf.sap.corp/velocity/vsystem/tests/e2e-test
  else
    pushd /go/src/github.wdf.sap.corp/velocity/vsystem/tests/deprecated-integration-test
  fi
    python3 run_scenarios.py --system-admin-user=system --system-admin-password=${VORA_SYSTEM_TENANT_PASSWORD} --log-level=DEBUG --junit-xml=result.xml ${ADDRESS} 2>&1 \
    | tee /infrabox/upload/archive/vsystem_e2e_test.log; exit ${PIPESTATUS[0]}
    JOB_STATUS=$?
    cat result.xml
    echo ${LOG_OUTPUT_DIR} /infrabox/upload/archive /infrabox/upload/testresult | xargs -n 1 cp result.xml
  popd
else
  if [ -d "/go/src/github.wdf.sap.corp/velocity/vsystem/tests/e2e-test-js" ];then
    pushd /go/src/github.wdf.sap.corp/velocity/vsystem/tests/e2e-test-js
  else
    pushd /go/src/github.wdf.sap.corp/velocity/vsystem/tests/integration-test
  fi
    # build new vctl
    rm -f /usr/local/bin/vctl
    go get -u github.com/jteeuwen/go-bindata
    go install github.com/jteeuwen/go-bindata/go-bindata
    ./update-vctl-js.sh
    if [ $? != 0 ];then
      die "build vctl for e2e-test-js failed!"
    fi
    ln -s $GOPATH/bin/vctl /usr/local/bin/vctl
    if [ -f "./main.js" ]; then
      JS_FILE="main.js"
    else
      JS_FILE="run-tests.js"
    fi
    vctl js ${JS_FILE} -- --address=${ADDRESS} --tenant=${VORA_TENANT} --user=${VORA_USERNAME} --password=${VORA_PASSWORD} 2>&1 \
    | tee /infrabox/upload/archive/vsystem_e2e_testi_js.log; exit ${PIPESTATUS[0]}
    JOB_STATUS=$?
    cp /infrabox/upload/archive/vsystem_e2e_testi_js.log ${LOG_OUTPUT_DIR}
  popd
fi

if [ $? != 0 ];then
  die "vsystem e2e scenario test failed! Please check the infrabox job report."
fi
echo "vsystem test done..."

rm -rf /go/src/github.wdf.sap.corp/velocity
