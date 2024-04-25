#!/bin/bash
set -x
KEY_FILE="/project/credential.json"
if [ -n "${PARENT_INSTALL_JOB}" ]; then
  if [ ! -f /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh ]; then
    echo "/infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh does not exist. Skip the current job"
    exit 0
  else
    source /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh
    cp /infrabox/inputs/${PARENT_INSTALL_JOB}/credential.json ${KEY_FILE}
  fi
else
  echo "## Skip sourcing env.sh, Using external env information..."
fi
source /project/common.sh

# start docker daemon
/usr/bin/dockerd &

if [[ "${PROVISION_PLATFORM}" == "GKE" ]]; then
  gcloud auth activate-service-account --key-file=${KEY_FILE}
  gcloud config set project sap-p-and-i-big-data-vora
  gcloud docker -a
  if [ $? != 0 ];then
    die "gcloud docker login failed."
  fi
  export DOCKER_REGISTRY="eu.gcr.io/sap-p-and-i-big-data-vora/${GCP_DOCKER_REGISTRY_SUFFIX}"
elif [[ "${PROVISION_PLATFORM}" == "GARDENER-AWS" ]]; then
  export DOCKER_REGISTRY="990498310577.dkr.ecr.eu-central-1.amazonaws.com"
  aws_access_key=$(jq '.AWS_ACCESS_KEY' ${KEY_FILE})
  aws_access_key=${aws_access_key//\"/} #strip "
  aws_secret_access=$(jq '.AWS_SECRET_KEY' ${KEY_FILE})
  aws_secret_access=${aws_secret_access//\"/} #strip "
  aws_region="eu-central-1"
  set +x
  aws configure set aws_access_key_id $aws_access_key 2>&1 >/dev/null
  aws configure set aws_secret_access_key $aws_secret_access 2>&1 >/dev/null
  aws configure set region $aws_region 2>&1 >/dev/null
  eval $(aws ecr get-login --no-include-email | sed 's|https://||') 2>&1 >/dev/null
  set -x
  aws ecr create-repository --repository-name="com.sap.datahub.linuxx86_64/tests"
elif [[ "${PROVISION_PLATFORM}" == "DHAAS-AWS" ]]; then
  export DOCKER_REGISTRY="726853116465.dkr.ecr.eu-central-1.amazonaws.com/dev"
  AWS_REGION="eu-central-1"
  set +x
  aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID 2>&1 >/dev/null
  aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY 2>&1 >/dev/null
  aws configure set region $AWS_REGION 2>&1 >/dev/null
  eval $(aws ecr get-login --no-include-email | sed 's|https://||') 2>&1 >/dev/null
  set -x
  aws ecr create-repository --repository-name="dev/com.sap.datahub.linuxx86_64/tests/echo-app"
fi

PID=
txc_pod=$(kubectl -n $NAMESPACE get po -l vora-component=tx-coordinator -o jsonpath='{.items[0].metadata.name}')
txc_port=$(kubectl get service vora-tx-coordinator-ext -n $NAMESPACE -o=jsonpath='{.spec.ports[?(@.name=="tc-ext")].port}')
if ! port_forward ${txc_pod} ${txc_port} pod; then
  cat << EOF >> /infrabox/upload/archive/error_msg.log
health_check: Connection to Data Hub Error(PORT FORWARD)
EOF
  die "## pord-forward failed!"  
fi
pf_tx_pid=${PID}

PID=
VREP_PORT=8736
vrep_pod=$(kubectl get pods -l datahub.sap.com/app-component=vrep -n $NAMESPACE | grep vrep | awk '{print $1}')
if ! port_forward $vrep_pod ${VREP_PORT} pod; then
  cat << EOF >> /infrabox/upload/archive/error_msg.log
health_check: Connection to Data Hub Error(PORT FORWARD)
EOF
  die "## pord-forward failed!"
fi
pf_vrep_pid=${PID}
sleep 10

export TXC_HOST=127.0.0.1
export TXC_PORT="${txc_port}"
export TXC_USER="system\\\\${VORA_USERNAME}"
export TXC_PWD="${VORA_SYSTEM_TENANT_PASSWORD}"

TEST_COMPONENT="vsystem"

LOG_OUTPUT_DIR="/infrabox/output/execution_log/vsystem"
mkdir -p $LOG_OUTPUT_DIR

GIT_SSL_NO_VERIFY=1
export PATH=$PATH:$GOROOT/bin:$GOPATH/bin

echo "## Start vsystem test..."
set -e
pushd /go/src/github.wdf.sap.corp/velocity
git config --global http.sslVerify false
git clone git@github.wdf.sap.corp:velocity/vsystem.git >/dev/null 2>&1
pushd /go/src/github.wdf.sap.corp/velocity/vsystem

if [[ "${CURRENT_COMPONENT}" == "${TEST_COMPONENT}" ]]; then
  set +e
  # only work for tests running as pv in vsystem repository
  checkout_component_by_pr "${TEST_COMPONENT}"
  if [ $? -ne 0 ]; then
    echo "## WARNING! checkout component repository by PR failed! use master branch by default!"
  fi
  set -e
else
  echo "VSYSTEM_VERSION=$VSYSTEM_VERSION" >> /infrabox/upload/archive/vsystem.ver
  if [ $VSYSTEM_VERSION ]; then
    VSYSTEM_TAG=$(git tag |grep $VSYSTEM_VERSION |grep "rel")
    if [ $VSYSTEM_TAG ]; then
      echo "VSYSTEM_TAG=$VSYSTEM_TAG" >> /infrabox/upload/archive/vsystem.ver
      echo "## checkout vsystem repository by tag: $VSYSTEM_TAG "
      git checkout -b e2e-push $VSYSTEM_TAG
    fi
  fi
fi
popd
git clone git@github.wdf.sap.corp:velocity/go-context-client.git >/dev/null 2>&1
git clone git@github.wdf.sap.corp:velocity/trc.git >/dev/null 2>&1
popd
set +e

if [ -d "/go/src/github.wdf.sap.corp/velocity/vsystem/e2e-test" ];then
  pushd /go/src/github.wdf.sap.corp/velocity/vsystem/e2e-test
else
  pushd /go/src/github.wdf.sap.corp/velocity/vsystem/tests/api-test
fi
git log -20 --date-order > /infrabox/upload/archive/recent_commit.log
cp /infrabox/upload/archive/recent_commit.log ${LOG_OUTPUT_DIR}
cp /project/config.json ./
kubectl config set-context $(kubectl config current-context) --namespace=$NAMESPACE
cp ${KUBECONFIG} ./admin.conf
# update the docker registry in config.json
if [[ ${PROVISION_PLATFORM} != "MONSOON" ]];then
  URL="$(echo ${VSYSTEM_ENDPOINT} | awk -F':' '{print $1":"$2}')/"
  ADDRESS="--address=${URL}"
else
  sed -i 's/"DOCKER_REGISTRY":.*$/"DOCKER_REGISTRY": "'https://${NODE_HOST}':5000",/' config.json
  ADDRESS=''
fi

# build and push echo-app
if [ -d "/go/src/github.wdf.sap.corp/velocity/vsystem/tests" ]; then
  pushd /go/src/github.wdf.sap.corp/velocity/vsystem/tests
    make
    if [ $? != 0 ];then
      die "build and push echo-app failed. abort the vsystem api test!"
    fi
  popd
fi

go get -u github.com/jstemmer/go-junit-report
EXTRA_OPTIONS="-test.run TestVoraAdapter"
if [[ -n "${CONTINUES_INTEGRATION}" ]] && [[ "${CONTINUES_INTEGRATION}" == "TRUE" ]]; then
  EXTRA_OPTIONS=""
fi

# watch the pods
kubectl get pods -w -n $NAMESPACE 2>&1 > /infrabox/upload/archive/pods_watch.log &
pf_pods_watch_pid=$!

export CGO_ENABLED=0
go test -timeout 14400s -v --traceLevel debug $ADDRESS ${EXTRA_OPTIONS} \
    --imagesRegistry=${DOCKER_REGISTRY} \
    --vrepAddress "https://localhost:${VREP_PORT}" \
    -systemAdminUsername $VORA_USERNAME -systemAdminPassword $VORA_SYSTEM_TENANT_PASSWORD -tags=releasePack 2>&1 \
    | tee /infrabox/upload/archive/vsystem_api_test.log \
    | go-junit-report > vsystem_report.xml; job_status=${PIPESTATUS[0]}
cat vsystem_report.xml
echo ${LOG_OUTPUT_DIR} /infrabox/upload/archive /infrabox/upload/testresult | xargs -n 1 cp vsystem_report.xml
# dump the k8s
dump_k8s_cluster_info
popd

if [[ ${job_status} -ne 0 ]];then
  echo "run vsystem_api_test failed! status code is ${job_status}"
  python /project/check_vsystem_result.py /infrabox/upload/testresult/vsystem_report.xml
  job_status=$?
  echo "after parsing test result, exit code is ${job_status}"
  exit ${job_status}
fi

echo "vsystem test done..."

kill $pf_tx_pid && wait $pf_tx_pid 2>/dev/null
kill $pf_vrep_pid && wait $pf_vrep_pid 2>/dev/null
kill $pf_pods_watch_pid && wait $pf_pods_watch_pid 2>/dev/null

rm -rf /go/src/github.wdf.sap.corp/velocity
