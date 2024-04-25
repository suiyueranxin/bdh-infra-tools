#!/bin/bash
set -x

function prepare() {
  source /project/common.sh
  if [[ -z ${JOB_ACTION} ]]; then
    export JOB_ACTION="Create"
  fi

  LOG_OUTPUT_DIR="/infrabox/output/execution_log"
  mkdir -p $LOG_OUTPUT_DIR
}

function create_prepare() {
  if [[ $UPGRADE_TEST == "yes" ]]; then
    pushd /project
      clone_hanalite_releasepack
    popd
    pushd /project/hanalite-releasepack
      if [[ -n "${VORA_VERSION}" ]]; then
        get_tag_by_version_and_branch ${VORA_VERSION} ${GERRIT_CHANGE_BRANCH}
        if [ $VORA_VERSION_TAG ]; then
          git checkout -b e2e-push $VORA_VERSION_TAG
          echo "## VORA_VERSION_TAG: ${VORA_VERSION_TAG}"
        fi
      fi

      if [[ ! $BASE_BDH_VERSION ]]; then
        die "No base version defined! for upgrade test"
      fi

      if [ -f "./upgrade_multi_base_version.json" ]; then
        #default version index
        INDEX=0
        if [[ ${BASE_VERSION_INDEX} ]]; then
          INDEX=${BASE_VERSION_INDEX}
        fi
        BASE_VERSION_INSTALLATION_OPTIONS=$(jq ".BASE_BDH_VERSION|.[${INDEX}]|.base_version_installation_options" "upgrade_multi_base_version.json")
        if [[ "$BASE_VERSION_INSTALLATION_OPTIONS" == "null" ]]; then
          BASE_VERSION_INSTALLATION_OPTIONS=
        fi
        TARGET_VERSION_INSTALLATION_OPTIONS=$(jq ".BASE_BDH_VERSION|.[${INDEX}]|.target_version_installation_options" "upgrade_multi_base_version.json")
        if [[ "$TARGET_VERSION_INSTALLATION_OPTIONS" == "null" ]]; then
          TARGET_VERSION_INSTALLATION_OPTIONS=
        fi
      fi

      export BASE_BDH_VERSION=${BASE_BDH_VERSION//\"/}
      echo "## Upgrade from Datahub version: $BASE_BDH_VERSION"
      echo "export BASE_BDH_VERSION=${BASE_BDH_VERSION}" >> /infrabox/upload/archive/bdh_base_version.sh
      if [[ -n ${BASE_VERSION_INSTALLATION_OPTIONS} ]]; then
        export BASE_VERSION_INSTALLATION_OPTIONS=${BASE_VERSION_INSTALLATION_OPTIONS//\"/}
        echo "export BASE_VERSION_INSTALLATION_OPTIONS=${BASE_VERSION_INSTALLATION_OPTIONS}" >> /infrabox/output/bdh_base_version.sh
      fi
      if [[ -n ${TARGET_VERSION_INSTALLATION_OPTIONS} ]]; then
        export TARGET_VERSION_INSTALLATION_OPTIONS=${TARGET_VERSION_INSTALLATION_OPTIONS//\"/}
        echo "export TARGET_VERSION_INSTALLATION_OPTIONS=${TARGET_VERSION_INSTALLATION_OPTIONS}" >> /infrabox/output/bdh_base_version.sh
      fi
    popd
  fi

  if [[ $PROVISION_PLATFORM == DHAAS* ]]; then
    pushd /project
      clone_hanalite_releasepack
    popd
    pushd /project/hanalite-releasepack
      if [[ -n "${VORA_VERSION}" ]]; then
        get_tag_by_version_and_branch ${VORA_VERSION} ${GERRIT_CHANGE_BRANCH}
        if [ $VORA_VERSION_TAG ]; then
          git checkout -b e2e-push $VORA_VERSION_TAG
          echo "## VORA_VERSION_TAG: ${VORA_VERSION_TAG}"
        fi
      fi

      get_component_version_from_pom
      echo "export RELEASEPACK_VERSION=${VORA_VERSION}" >> /infrabox/output/env.sh
      echo "export PROVISION_PLATFORM=${PROVISION_PLATFORM}" >> /infrabox/output/bdh_base_version.sh
      get_current_job_name
      echo "export KUBECONFIG=/infrabox/inputs/${CURRENT_JOB_NAME}/admin.conf" >> /infrabox/output/bdh_base_version.sh
      if [[ $GERRIT_CHANGE_BRANCH ]] && [[ "$GERRIT_CHANGE_BRANCH" != "master" ]]; then
        echo "export GERRIT_CHANGE_BRANCH=${GERRIT_CHANGE_BRANCH}" >> /infrabox/output/bdh_base_version.sh
      fi
      if [ $GERRIT_PATCHSET_REF ];then
        echo "export GERRIT_PATCHSET_REF=${GERRIT_PATCHSET_REF}" >> /infrabox/output/bdh_base_version.sh
      fi
      # copy import.sh & export.sh out for import_export_test job
      cp src/main/kubernetes/tools/*.sh /infrabox/output/
    popd
  fi
}

function get_kubeconfig_from_existing_cluster() {
  if [[ -f /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt ]] && \
     [[ -f /infrabox/inputs/${K8S_CREATION_JOB}/admin.conf ]]; then

    cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt
    cluster_name=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/k8s_cluster.txt)
    export K8S_CLUSTER_NAME=$cluster_name
    echo "K8S_CLUSTER_NAME " $cluster_name
    cat /infrabox/inputs/${K8S_CREATION_JOB}/admin.conf
    export KUBECONFIG="/infrabox/inputs/${K8S_CREATION_JOB}/admin.conf"
    get_current_job_name
    echo "export KUBECONFIG=/infrabox/inputs/${CURRENT_JOB_NAME}/admin.conf" >> /infrabox/output/env.sh
  else
    echo "## No DI cluster to ${JOB_ACTION}"
    exit 1
  fi
}
function expose_vsystem_svc() {
  export KUBECONFIG=/infrabox/output/admin.conf
  kubectl -n ${NAMESPACE} get service vsystem-ext
  if [ $? == 0 ]; then
    echo "service vsystem-ext already exists"
    return 0
  fi

  kubectl -n ${NAMESPACE} expose service vsystem --type NodePort --name=vsystem-ext
  if [ $? != 0 ]; then
    echo "## Expose vsystem service failed!"
    exit 1
  fi
  kubectl -n ${NAMESPACE} patch service vsystem-ext -p '{"spec": {"ports" : [{"name": "vsystem-ext", "port" : 8797}]}}'
  if [ $? != 0 ]; then
    echo "## Patch service vsystem-ext failed!"
    exit 1
  fi
  kubectl -n ${NAMESPACE} annotate service vsystem-ext service.beta.kubernetes.io/app-protocols='{"vsystem-ext":"HTTPS"}'
  if [ $? != 0 ]; then
    echo "## Annotate Patch service vsystem-ext failed!"
    exit 1
  fi
}

function version_ge(){
  test "$(echo "$@" | tr " " "\n" | sort -rV | head -n 1)" == "$1"; }

function export_achieve_files() {
  if [ -f /infrabox/output/create_k8s_cluster.log ]; then
    cp -rf /infrabox/output/create_k8s_cluster.log  ${LOG_OUTPUT_DIR}/create_k8s_cluster.log
    cp -rf /infrabox/output/create_k8s_cluster.log /infrabox/upload/archive/create_k8s_cluster.log
  fi

  if [ -f /infrabox/output/k8s_cluster.txt ]; then
    cat /infrabox/output/k8s_cluster.txt >> /infrabox/upload/archive/k8s_cluster.txt
  fi

  if [ -f /infrabox/output/admin.conf ]; then
    cp -rf /infrabox/output/admin.conf /infrabox/upload/archive/admin.conf
    cat /infrabox/output/admin.conf
    get_current_job_name
    echo "export KUBECONFIG=/infrabox/inputs/${CURRENT_JOB_NAME}/admin.conf" >> /infrabox/output/env.sh
  fi

  if [[ -f /infrabox/output/k8s_namespace.txt ]]; then
    cat /infrabox/output/k8s_namespace.txt >> /infrabox/upload/archive/k8s_namespace.txt
  fi

  if [[ -f /infrabox/output/azure_cert_file.sh ]]; then
    cat /infrabox/output/azure_cert_file.sh >> /infrabox/upload/archive/azure_cert_file.sh
    cat /infrabox/output/azure_cert_file.sh >> /infrabox/output/env.sh
  fi

  if [[ -f /infrabox/output/bdh_base_version.sh ]]; then
    if [[ -f /infrabox/output/k8s_cluster.txt ]]; then
      K8S_CLUSTER_NAME=$(cat /infrabox/output/k8s_cluster.txt)
      echo "export K8S_CLUSTER_NAME=${K8S_CLUSTER_NAME}" >> /infrabox/output/bdh_base_version.sh
    fi
    if [[ -f /infrabox/output/k8s_version.txt ]]; then
      K8S_VERSION=$(cat /infrabox/output/k8s_version.txt)
      echo "export K8S_VERSION=${K8S_VERSION}" >> /infrabox/output/bdh_base_version.sh
    fi
    source /infrabox/output/bdh_base_version.sh
    if [[ -n ${VSYSTEM_ENDPOINT} ]]; then
      temp_str=$(echo ${VSYSTEM_ENDPOINT#*//})
      NODE_HOST=$(echo ${temp_str%:*})
      echo "export NODE_HOST=${NODE_HOST}" >> /infrabox/output/bdh_base_version.sh
      echo "export NODE_PORT=443" >> /infrabox/output/bdh_base_version.sh
    fi

    RETRY=6
    if [[ $PROVISION_PLATFORM == DHAAS* ]] && \
      ([[ "${JOB_ACTION}" == "Create" ]] || [[ "${JOB_ACTION}" == "Restore" ]]); then
      export KUBECONFIG=/infrabox/output/admin.conf
      if [[ "${JOB_ACTION}" == "Create" ]]; then
        echo "## create vflow instacne"
        if [[ ! -f vctl ]]; then
          download_vctl
          cp ./vctl /infrabox/output/vctl
        fi
        for ((i = 1; i <= ${RETRY}; i++)); do
          # DM01-2802 from vsolution 2210.6.0, no need to start pipeline-modeler
          if [[ -n "${VSOLUTION_VERSION}" ]]; then
            if version_ge "${VSOLUTION_VERSION}" "2210.6.0"; then
              break
            fi
          fi

          vctl login ${VSYSTEM_ENDPOINT} ${VORA_TENANT} ${VORA_USERNAME} -p ${VORA_PASSWORD} --insecure
                # change tracer log level to debug
          vctl parameter set vflow.traceLevel debug --tenant=${VORA_TENANT}
          vctl scheduler start pipeline-modeler
          # wait pods up
          sleep 30s
          VFLOW_POD=$(kubectl get pods -l vora-component=vflow,vsystem.datahub.sap.com/user=${VORA_USERNAME},vsystem.datahub.sap.com/tenant=${VORA_TENANT} -n ${NAMESPACE} -o go-template --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')
          if [ -z "${VFLOW_POD}" ]; then
            if [[ $i < ${RETRY} ]]; then
              echo "create instance failed. Retry..."
              sleep 1m
              continue
            fi
            echo "## Warning! Create vflow instance failed!"
          else
            vctl parameter set vflow.traceLevel info --tenant=${VORA_TENANT}
            break
          fi
        done
      fi
      expose_vsystem_svc
      kubectl create -f /project/add_white_list.yaml	
      if [ $? != 0 ]; then	
        echo "## Warning! Add DI instance to white list failed!"	
      fi
    fi

    if [[ "${JOB_ACTION}" == "Upgrade" ]]; then
      echo "export CONTAINER_REGISTRY_ADDRESS=" >> /infrabox/output/bdh_base_version.sh
    fi

    cat /infrabox/output/bdh_base_version.sh >> /infrabox/upload/archive/bdh_base_version.sh
    cat /infrabox/output/bdh_base_version.sh >> /infrabox/output/env.sh

    # Health Check
    echo "## BDH Health Check"
    #echo "skip cluster check"
    #export SKIP_CLUSTER_CHECK="yes"
    echo "run cluster check for more stable"
    python /project/bdh_health_check.py
    HEALTH_CHECK_RESULT=$?

    if [ $HEALTH_CHECK_RESULT != 0 ]; then
      echo "## Health Check failed!"
      exit 1
    fi
    echo "## Health Check is done!"

    def_conn --action=load_driver
    LOAD_DB_DRIVER_RESULT=$?

    if [ $LOAD_DB_DRIVER_RESULT -ne 0 ]; then
      echo "## Load db driver failed!"
      exit 1
    fi
    echo "## Load db driver is done!"
  fi
}

function prepare_env_file() {
  if [ -d "/project/hanalite-releasepack/" ]; then
    rm -rf /project/hanalite-releasepack
  fi
  pushd /project
    repo="ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack"
    clone_repo $repo
    if [ $? -ne 0 ]; then
      echo "clone ${repo} failed"
      exit 1
    fi
    pushd /project/hanalite-releasepack
      get_tag_by_version_and_branch ${VORA_VERSION} ${GERRIT_CHANGE_BRANCH}
      if [ $VORA_VERSION_TAG ]; then
        git checkout -b e2e-push $VORA_VERSION_TAG
        echo "## VORA_VERSION_TAG: ${VORA_VERSION_TAG}"
      fi
      source /infrabox/output/env.sh
      if [ -z "${ALL_COMPONENTS_VERSIONS}" ]; then
        get_component_version_from_pom
      fi
      echo "export RELEASEPACK_VERSION=${VORA_VERSION}" >> /infrabox/output/env.sh
    popd
  popd
  echo "export PROVISION_PLATFORM=${PROVISION_PLATFORM}" >> /infrabox/output/env.sh
}

function put_cluster_info_into_env_file() {
  if [ -f "/infrabox/output/k8s_cluster.txt" ] && [ -f "/infrabox/output/auth_header.txt" ]; then
    K8S_CLUSTER_NAME=$(cat /infrabox/output/k8s_cluster.txt)
    AUTH_HEADER=$(cat /infrabox/output/auth_header.txt)
    python /project/get_cloud_credentials.py ${K8S_CLUSTER_NAME} ${PROVISION_PLATFORM} "/" "${AUTH_HEADER}"
    cp /credential.json /infrabox/output/credential.json
    if [[ "${PROVISION_PLATFORM}" == "GKE" ]]; then
      echo "export GCP_DOCKER_REGISTRY_SUFFIX=${K8S_CLUSTER_NAME}" >> /infrabox/output/env.sh
    elif [[ "${PROVISION_PLATFORM}" == "AWS-EKS" ]]; then
      echo "export EKS_VFLOW_DOCKER_REGISTRY_SUFFIX=${K8S_CLUSTER_NAME}" >> /infrabox/output/env.sh
    elif [[ "${PROVISION_PLATFORM}" == "AZURE-AKS" ]]; then
      if [-f "/infrabox/output/k8s_info.sh" ]; then
        cat /infrabox/output/k8s_info.sh >> /infrabox/output/env.sh
      fi
    fi
  fi
}

function export_env() {
  if [[ -f /infrabox/output/env.sh ]]; then
    cat /infrabox/output/env.sh >> /infrabox/upload/archive/env.sh
  fi
}

# ----------------------------------------------------------------
prepare
echo "## ${JOB_ACTION} kubernetes cluster start..."

case ${JOB_ACTION} in
  "Create")
    create_prepare
    ;;
  "Upgrade")
    get_kubeconfig_from_existing_cluster
    ;;
  "Backup")
    get_kubeconfig_from_existing_cluster
    ;;
  "Restore")
    get_kubeconfig_from_existing_cluster
    ;;
  "Hibernate")
    get_kubeconfig_from_existing_cluster
    ;;
  "Wakeup")
    get_kubeconfig_from_existing_cluster
    ;;
esac


python /project/create_k8s.py
TEST_RETURN_VALUE=$?
if [ ${TEST_RETURN_VALUE} -ne 0 ];then
  echo "${JOB_ACTION} Kubernetes cluster failed!"
  exit ${TEST_RETURN_VALUE}
fi

export_achieve_files

case ${JOB_ACTION} in
  "Create")
    if [[ "${UPGRADE_TEST}" == "yes" ]]; then
      expose_vsystem_svc
      prepare_env_file
      put_cluster_info_into_env_file
    fi
    export_env
    ;;
  "Upgrade")
    prepare_env_file
    export_env
    ;;
  "Backup")
    ;;
  "Restore")
    prepare_env_file
    export_env
    ;;
  "Hibernate")
    ;;
  "Wakeup")
    ;;
esac

echo "$JOB_ACTION Kubernetes cluster end..."
