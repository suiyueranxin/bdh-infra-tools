#!/bin/bash
set -ex
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

echo "## hanawire test start..."

## port-forward to for connection to hana and hanawire for external access to cloud service and clusterIP service
hana_pod=$(kubectl -n $NAMESPACE get po |grep hana | awk 'NR==1 {print $1}')
kubectl --namespace=$NAMESPACE port-forward ${hana_pod} 30017 > /dev/null &
hana_pf_pid=$!
txc_pod=$(kubectl -n $NAMESPACE get po |grep tx-coordinator | awk 'NR==1 {print $1}')
kubectl --namespace=$NAMESPACE port-forward ${txc_pod} 30115 > /dev/null &
hw_pf_pid=$!
sleep 1
export HANA_HOST=127.0.0.1
export HANA_PORT=30017
export HW_HOST=127.0.0.1
export HW_PORT=30115
export HW_CONNECT_VORA_INTERNAL_K8S=True
export USE_K8S_HANA=True
export HW_ENABLE_TLS=True
export VORA_TENANT=system
export VORA_USERNAME=system
if [[ $VORA_SYSTEM_TENANT_PASSWORD ]] ; then
  export VORA_PASSWORD=$VORA_SYSTEM_TENANT_PASSWORD
fi

git config --global http.sslVerify false
git clone git@github.wdf.sap.corp:I063095/hanawire.git
pushd hanawire
git checkout hdbsql-nightly-run

#echo "Copy hdbcli python driver"
tar -xvf driver/hdb_python_driver.tar.gz -C /usr/lib/python2.7
echo "Download hdbsql"
wget  --no-check-certificat https://int.repositories.cloud.sap/artifactory/build-milestones/com/sap/hana/clients/linuxx86_64/release/gcc5/client-hdbsql/2.4.21-ms/client-hdbsql-2.4.21-ms-linuxx86_64.tar.gz && tar -xvf client-hdbsql-2.4.21-ms-linuxx86_64.tar.gz -C driver/
echo "Set configuration parameters before kickoff test"
./use_builtin_vora_hana.py

set +e
echo "Kick off test..."
#pytest test_hanawire.py -v -s --junit-xml=/infrabox/upload/testresult/hanawire.xml
pytest test_hanawire_hdbsql.py -v -s --junit-xml=/infrabox/upload/testresult/hanawire.xml
TEST_RETURN_VALUE=$?

kill $hana_pf_pid
kill $hw_pf_pid
wait $hana_pf_pid 2>/dev/null
wait $hw_pf_pid 2>/dev/null

set -e
popd

if [ ${TEST_RETURN_VALUE} != 0 ];then
  echo "hanawire test failed! Please check the infrabox job report."
  exit 1
fi

echo "hanawire test done..."
