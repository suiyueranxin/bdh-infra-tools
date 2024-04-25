#!/bin/bash
set -x

echo "## Start trigger DI backup ..."

if [ -n "${PARENT_INSTALL_JOB}" ]; then
    if [ -f /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh ]; then
        source /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh
        if [ -z "${KUBECONFIG}" ]; then
            export KUBECONFIG="/infrabox/inputs/${PARENT_INSTALL_JOB}/admin.conf"
        fi
        if [ -z "${NAMESPACE}" ]; then
            echo "### [level=error] No namespace defined in env.sh, exit"
            exit 1
        fi
    else
        echo "### [level=error] No env file found from output of ${PARENT_INSTALL_JOB}"
        exit 1
    fi
else
    echo "### [level=error] No install job defined, exit"
    exit 1
fi
wait_backup_ready() {
    get_backup_cr_retry_num=40
    check_status_retry_num=60
    backup_cr=""
    for i in $(seq 1 $get_backup_cr_retry_num); do
        backup_cr=`kubectl -n ${NAMESPACE} get bak --sort-by=.metadata.creationTimestamp | tail -n -1 | awk -F ' ' '{print $1}'`
        if [ "${backup_cr}" != "" ]; then
            break
        else
            sleep 15s
        fi
    done
    if [ "${backup_cr}" == "" ]; then
        echo "### [level=error] Can't get correct backup CR in 10 mins, exit"
        exit 1
    fi
    backup_state=""
    for i in $(seq 1 $check_status_retry_num); do
        backup_state=`kubectl -n ${NAMESPACE} get bak ${backup_cr} -o jsonpath='{.status.state}'`
        if [ "${backup_state}" == "Ready" ]; then
            break
        else
            sleep 30
        fi
    done
    if [ "${backup_state}" != "Ready" ]; then
        echo "### [level=error] Backup CR ${backup_cr} NOT ready in 30 mins, exit"
        exit 1
    fi
}

trigger_snapshot_backup() {
    DI_SYSTEM_NAMESPACE=datahub-system
    remotePath="$( kubectl get datahubs default -o=jsonpath='{.spec.backupRemotePath}' -n ${NAMESPACE} )"
    echo "remotePath = $remotePath"
    kubectl exec -it $(kubectl get pod -n ${DI_SYSTEM_NAMESPACE}|grep "datahub-operator"|awk '{print $1}') -n ${DI_SYSTEM_NAMESPACE} --  dhinstaller backup -n ${NAMESPACE} --backup-remote-path ${remotePath}
    if [ $? != 0 ]; then
        mkdir -p /tmp/dump_k8s
        kubectl cluster-info dump --output-directory=/tmp/dump_k8s/ --all-namespaces
        tar -cvzf /infrabox/upload/archive/k8s_dump.tar.gz /tmp/dump_k8s
        echo "### [level=error] trigger snapshot backup failed"
        exit 1
    fi	
}
wait_backup_ready
trigger_snapshot_backup
wait_backup_ready

if [ -z $backup_cr ]; then
    echo "### [level=error] No correct backup CR sepecified, trigger snapshot backup failed"
    exit 1        
fi
if [ -z $remotePath ]; then
    echo "### [level=error] No correct remote path for backup, trigger snapshot backup failed"
    exit 1        
fi
backup_time=`date +"%Y-%m-%d %H:%M:%S"`
backup_timestamp=`date -d "$backup_time" +%s`
system_id=`kubectl -n ${NAMESPACE} get bak ${backup_cr} -o jsonpath='{.spec.clusterID}'`
echo "export DI_BACKUP_NAME=${remotePath}/${system_id}/${backup_timestamp}" >> /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh
cp /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh /infrabox/output/env.sh
cp /infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh /infrabox/upload/archive/env.sh