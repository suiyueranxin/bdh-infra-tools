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
echo "dump all cluster logs"
dump_k8s_cluster_info

echo "## DI diagnostics-prometheus"
if [ -n "${PROMETHEUS}" ] && [[ "${PROMETHEUS}" == "TRUE" ]]; then
  python /project/prometheus.py
  if [ $? -eq 0 ]; then
    cp CPU_Load.png Memory.png /infrabox/upload/archive/
  fi
fi

echo "## log collection by elasticsearch start..."
elastic_pod=$(kubectl -n $NAMESPACE get pods -l datahub.sap.com/app-component=elasticsearch -o jsonpath='{.items[0].metadata.name}')
(
    while true; do
        kubectl port-forward -n=$NAMESPACE $elastic_pod 10010:9200 > /dev/null
        echo "Reestablishing port forwarding to elastic pod"
    done
) &
pf_pid=$!
# since we spawn a background process, we should wait for it to be ready
sleep 10
export NODE_HOST=127.0.0.1
export ePort=10010

echo "master address is " $NODE_HOST
echo "elasticsearch port is" $ePort

python /project/log_collection.py
tar -cvzf /infrabox/output/k8s_vora_log.tar.gz /tmp/k8s_vora_log
cp /infrabox/output/k8s_vora_log.tar.gz /infrabox/upload/archive

pushd /infrabox/context
ls -l
popd

kill $pf_pid
wait $pf_pid 2>/dev/null

echo "log collection done..."
