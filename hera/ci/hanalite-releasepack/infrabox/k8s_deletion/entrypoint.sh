#!/bin/bash
set -x

echo "## Delete kubernetes cluster start..."

LOG_OUTPUT_DIR="/infrabox/output/execution_log"
mkdir -p $LOG_OUTPUT_DIR

if [ -z "$SERVER_URL" ];then
    base_url='https://im-api.datahub.only.sap'
else
    base_url=$SERVER_URL
fi

if [ -f /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt ];then
    cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt
    #while read cluster_name
    #do
    #    echo "delete kubernetes cluster " $cluster_name
    #    curl -ikL -X DELETE $base_url/api/v1/tasks/$cluster_name 2>&1 | tee -a  $LOG_OUTPUT_DIR/delete_k8s_cluster.log 
    #done < /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt
    cluster_name=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt)
    export CLUSTER_NAME=$cluster_name
    if [[ -z "${RESERVE_CLUSTER}" ]]; then
        echo "delete kubernetes cluster " $cluster_name
        if [ -z "$ENABLE_AUTH_HEADER" ] || [ "$ENABLE_AUTH_HEADER" == "yes" ]; then
            auth_header=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/auth_header.txt)
            curl -ikL -X DELETE -H "${auth_header}" $base_url/api/v1/tasks/$cluster_name 2>&1 | tee -a  $LOG_OUTPUT_DIR/delete_k8s_cluster.log
        else
            curl -ikL -X DELETE $base_url/api/v1/tasks/$cluster_name 2>&1 | tee -a  $LOG_OUTPUT_DIR/delete_k8s_cluster.log
        fi
    else
        python /project/reserve_cluster.py
    fi
else
    echo "No k8s cluster to cleanup"
fi

echo "Delete Kubernetes cluster done, not return status to avoid affect the build execution result..."

