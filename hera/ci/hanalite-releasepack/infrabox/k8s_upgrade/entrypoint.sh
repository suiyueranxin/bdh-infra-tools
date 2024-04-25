#!/bin/bash

set -x

if [[ -f /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt ]] && [[ -f /infrabox/inputs/${K8S_CREATION_JOB}/admin.conf ]];then

    cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt
    cluster_name=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt)
    export K8S_CLUSTER_NAME=$cluster_name
    echo "K8S_CLUSTER_NAME " $cluster_name

    UPGRADE_TO_FILE="/infrabox/inputs/${K8S_CREATION_JOB}/k8s_upgrade_to.txt"
    if [[ -f ${UPGRADE_TO_FILE} ]]; then
        export K8S_VERSION_UPGRADE_TO=$(cat ${UPGRADE_TO_FILE})
    fi 

    cat /infrabox/inputs/${K8S_CREATION_JOB}/admin.conf
    export KUBECONFIG="/infrabox/inputs/${K8S_CREATION_JOB}/admin.conf"

    # Get the environment from env.sh
    if [ -n "${PARENT_INSTALL_JOB}" ]; then
        ENV_FILE="/infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh"
        if [ ! -f ${ENV_FILE} ]; then
            echo "${ENV_FILE} does not exist. Skip the current job"
            exit 1
        else
            source ${ENV_FILE}
        fi
    fi

    python /project/k8s_upgrade/k8s_upgrade.py

    if [ $? != 0 ]; then
        echo "## k8s cluster failed!"
        exit 1
    fi
else
    echo "## No k8s cluster to upgrade"
    exit 1
fi

echo "## k8s upgrade success!"
