####################################################
### These funcitons are shared by jenkins jobs.
### Please use the same parameter name in jenkins
### Modify bootstrap_cluster_on_demand whenever a new parameter is added
### after sourcing this file, you can just run the playbook as follow:
### bootstrap_cluster_on_demand "ansible-playbook -i HOSTFILE PLAYBOOK"
####################################################

# param 1: version string with format x.x.x
source $(dirname ${BASH_SOURCE[0]})/utils.sh

WORKSPACE=${WORKSPACE:-/tmp}
BUILD_NUMBER=${BUILD_NUMBER:-0}

function parse_version()
{
  [ -z $1 ] && die "please provide a version number"
  read -a VERSION <<< "$(echo "$1" | sed 's/[.]/ /g' | sed 's/ /./g4')"
  VERSION_MAJOR="${VERSION[0]}"
  VERSION_MINOR="${VERSION[1]}"
  VERSION_PATCH="${VERSION[2]}"
  [ -z ${VERSION[3]} ] && VERSION_ARTIFACT="0" || VERSION_ARTIFACT="${VERSION[3]}"
}

function set_cluster_node_prefix(){
  #verify the email format and set MASTER_NAME and WORKER_NAME_PREFIX
  str=`echo $EMAIL | awk '/^([a-zA-Z0-9_\-\.\+]+)@sap.com/{print $0}'`
  if [ ! -n "${str}" ];then
    echo "ERROR: email error, please input right email."
    exit 1
  else
    # replace '.' to '-' and get the name of the email: my.name@sap.com -> my_name
    email_string=$(echo ${EMAIL%%@*} | sed 's/\./-/g')
    if [ x${PROJECT_NAME} == "xhanaxsbdh" ];then
       HANA_HOST_NAME="${email_string}-${BUILD_NUMBER}-${PROJECT_NAME}"
       GCP_HANA_INSTANCE_NAME="${email_string}-${BUILD_NUMBER}-${PROJECT_NAME}"
    elif [ x${PROJECT_NAME} == 'xhadoop' ];then
       MASTER_NAME="${email_string}-${BUILD_NUMBER}-${PROJECT_NAME}-master"
       WORKER_NAME_PREFIX="${email_string}-${BUILD_NUMBER}-${PROJECT_NAME}-worker"
    elif [ x${CLOUD_PLATFORM} == 'xazure' ];then
       AZURE_K8S_CLUSTER_NAME="${email_string}-${INFRABOX_BUILD_NUMBER}"
    elif [ x${CLOUD_PLATFORM} == 'xazure-aks' ] && [ -z $AKS_CLUSTER_NAME ];then
       AKS_CLUSTER_NAME="${email_string}-${BUILD_NUMBER}"
    elif [ x${CLOUD_PLATFORM} == 'xkops' ] && [ -z $KOPS_K8S_CLUSTER_NAME ];then
       owner=$(echo "$OWNER" | tr '[:upper:]' '[:lower:]')
       KOPS_K8S_CLUSTER_NAME="${owner}-${BUILD_NUMBER}"
    elif [ x${CLOUD_PLATFORM} == 'xgke' ] && [ -z $GKE_K8S_CLUSTER_NAME ];then
       GKE_K8S_CLUSTER_NAME=$(echo ${email_string}-${BUILD_NUMBER} | sed 's/_/-/g')
    elif [ x${CLOUD_PLATFORM} == 'xgardener-aws' ] && [ -z $GARDENER_AWS_K8S_CLUSTER_NAME ];then
       GARDENER_AWS_K8S_CLUSTER_NAME="${email_string}-${BUILD_NUMBER}"
    elif [ x${CLOUD_PLATFORM} == 'xeks' ] && [ -z $EKS_K8S_CLUSTER_NAME ];then
       EKS_K8S_CLUSTER_NAME=$(echo ${email_string}-${BUILD_NUMBER} | sed 's/_/-/g')
    else
       GCP_INSTANCE_NAME="${email_string}-${BUILD_NUMBER}-${PROJECT_NAME}"
       MASTER_NAME="${email_string}-${BUILD_NUMBER}-${PROJECT_NAME}-master"
       WORKER_NAME_PREFIX="${email_string}-${BUILD_NUMBER}-${PROJECT_NAME}-worker"
    fi
    if [ -n "$CLUSTER_NAME" ]; then
       GKE_K8S_CLUSTER_NAME=$CLUSTER_NAME
       KOPS_K8S_CLUSTER_NAME=$CLUSTER_NAME
       AKS_CLUSTER_NAME=$CLUSTER_NAME
       AZURE_K8S_CLUSTER_NAME=$CLUSTER_NAME
       GARDENER_AWS_K8S_CLUSTER_NAME=$CLUSTER_NAME
    fi
  fi
}

# This method replaces the last "}'" string with the extra variable string if "extra-vars" is already there; otherwise, append it instead
# $1 is the variables to append (with strict Json format!)
function append_variable()
{
  if  echo "$deploy_cmd" | grep -q "extra-vars"; then
    deploy_cmd=${deploy_cmd/%\}\'/,$1\}\'}
  else
    deploy_cmd="$deploy_cmd --extra-vars '{$1}'"
  fi
}

# This method appends the variables passed to ansible playbook in Json format (other format doesn't work with nested variables!)
# $1 is the ansible playbook command
function bootstrap_cluster_on_demand()
{
  deploy_cmd="$1"
  # Parameters for Non-docker clusters
  if [ -n "$AWS_ACCESS_KEY" ]; then
    append_variable "\"aws_access_key\":\"$AWS_ACCESS_KEY\""
  fi
  if [ -n "$AWS_SECRET_KEY" ]; then
    append_variable "\"aws_secret_key\":\"$AWS_SECRET_KEY\""
  fi
  if [ -n "$AWS_SECURITY_JSON_FILE" ]; then
    append_variable "\"security_json_file\":\"$AWS_SECURITY_JSON_FILE\""
  fi
  if [ -n "$GARDENER_SECURITY_FILE" ]; then
    append_variable "\"gardener_security_file\":\"$GARDENER_SECURITY_FILE\""
  fi
  if [ -n "$AKS_SECURITY_JSON_FILE" ]; then
    append_variable "\"security_json_file\":\"$AKS_SECURITY_JSON_FILE\""
  fi
  if [ -n "$CCLOUD_SECURITY_JSON_FILE" ]; then
    append_variable "\"security_json_file\":\"$CCLOUD_SECURITY_JSON_FILE\""
  fi
  if [ -n "$MONSOON_REGION" ]; then
    append_variable "\"monsoon_region\":\"$MONSOON_REGION\""
  fi
  if [ -n "$CCLOUD_OS_REGION_NAME" ]; then
    append_variable "\"ccloud_os_region_name\":\"$CCLOUD_OS_REGION_NAME\""
  fi
  if [ -n "$CCLOUD_OS_PROJECT_NAME" ]; then
    append_variable "\"ccloud_os_project_name\":\"$CCLOUD_OS_PROJECT_NAME\""
  fi
  if [ -n "$CCLOUD_OS_USERNAME" ]; then
    append_variable "\"ccloud_common_account\":\"$CCLOUD_OS_USERNAME\""
  fi
  if [ -n "$CCLOUD_OS_PASSWORD" ]; then
    append_variable "\"ccloud_common_account_password\":\"$(echo $CCLOUD_OS_PASSWORD | base64)\""
  fi
  if [ -n "$CCLOUD_PRIVATE_NETWORK_ID" ]; then
    append_variable "\"ccloud_private_network_id\":\"$CCLOUD_PRIVATE_NETWORK_ID\""
  fi
  if [ -n "$CCLOUD_XTERNAL_NETWORK_ID" ]; then
    append_variable "\"ccloud_external_network_id\":\"$CCLOUD_XTERNAL_NETWORK_ID\""
  fi
  if [ -n "$CCLOUD_DNS_ZONE_NAME" ]; then
    append_variable "\"ccloud_dns_zone_name\":\"$CCLOUD_DNS_ZONE_NAME\""
  fi
  if [ -n "$CCLOUD_DNS_ZONE_ID" ]; then
    append_variable "\"ccloud_dns_zone_id\":\"$CCLOUD_DNS_ZONE_ID\""
  fi
  if [ -n "$CCLOUD_KEY_NAME" ]; then
    append_variable "\"ccloud_key_name\":\"$CCLOUD_KEY_NAME\""
  fi
  if [ -n "$CCLOUD_SECURITY_GROUPS" ]; then
    append_variable "\"ccloud_security_groups\":\"$CCLOUD_SECURITY_GROUPS\""
  fi
  if [ -n "$CCLOUD_AVAILABILITY_ZONE" ]; then
    append_variable "\"ccloud_availability_zone\":\"$CCLOUD_AVAILABILITY_ZONE\""
  fi
    if [ -n "$GARDENER_PROJECT_NAME" ]; then
    append_variable "\"gardener_project_name\":\"$GARDENER_PROJECT_NAME\""
  fi
  if [ -n "$GARDENER_PROJECT_EXT_NETWORK_SUFFIX" ]; then
    append_variable "\"gardener_project_ext_network_suffix\":\"$GARDENER_PROJECT_EXT_NETWORK_SUFFIX\""
  fi
  if [ -n "$GARDENER_PROJECT_SECRET" ]; then
    append_variable "\"gardener_project_secret\":\"$GARDENER_PROJECT_SECRET\""
  fi
  if [ -n "$GARDENER_CCLOUD_IMAGE_TYPE" ]; then
    append_variable "\"gardener_ccloud_image_type_name\":\"$(echo $GARDENER_CCLOUD_IMAGE_TYPE |awk -F '--' '{print $1}')\""
    append_variable "\"gardener_ccloud_image_type_version\":\"$(echo $GARDENER_CCLOUD_IMAGE_TYPE |awk -F '--' '{print $2}')\""
  fi
  if [ -n "$GARDENER_CCLOUD_WORKER_INSTANCE_TYPE" ]; then
    append_variable "\"gardener_ccloud_worker_instance_type\":\"$GARDENER_CCLOUD_WORKER_INSTANCE_TYPE\""
  fi
  if [ -n "$MINIO_ACCESS_KEY" ]; then
    append_variable "\"minio_access_key\":\"$MINIO_ACCESS_KEY\""
  fi
  if [ -n "$MINIO_SECRET_KEY" ]; then
    append_variable "\"minio_secret_key\":\"$MINIO_SECRET_KEY\""
  fi
  if [ -n "$MINIO_URL" ]; then
    append_variable "\"minio_url\":\"$MINIO_URL\""
  fi
  if [ -n "$S3_ACCESS_KEY" ]; then
    append_variable "\"s3_access_key\":\"$S3_ACCESS_KEY\""
  fi
  if [ -n "$S3_SECRET_ACCESS_KEY" ]; then
    append_variable "\"s3_secret_access_key\":\"$S3_SECRET_ACCESS_KEY\""
  fi
  if [ -n "$MASTER_IMAGE" ]; then
    append_variable "\"master_image\":\"$MASTER_IMAGE\""
  fi
  if [ -n "$WORKER_IMAGE" ]; then
    append_variable "\"worker_image\":\"$WORKER_IMAGE\""
  fi
  if [ -n "$MONSOON_AVAILABILITY_ZONE" ]; then
    append_variable "\"monsoon_zone\":\"$MONSOON_AVAILABILITY_ZONE\""
  fi
  if [ -n "$EC2_URL" ]; then
    append_variable "\"ec2_endpoint_url\":\"$EC2_URL\""
  fi
  if [ -n "$MONSOON_IMAGE" ]; then
    append_variable "\"master_image\":\"$MONSOON_IMAGE\""
    append_variable "\"worker_image\":\"$MONSOON_IMAGE\""
  fi
  if [ -n "$MONSOON_MASTER_INSTANCE_TYPE" ]; then
    append_variable "\"master_instance_type\":\"$MONSOON_MASTER_INSTANCE_TYPE\""
  fi
  if [ -n "$MONSOON_WORKER_INSTANCE_TYPE" ]; then
    append_variable "\"worker_instance_type\":\"$MONSOON_WORKER_INSTANCE_TYPE\""
  fi
  if [ -n "$CCLOUD_IMAGE" ]; then
    append_variable "\"master_image\":\"$CCLOUD_IMAGE\""
    append_variable "\"worker_image\":\"$CCLOUD_IMAGE\""
  fi
  if [ -n "$CCLOUD_MASTER_INSTANCE_TYPE" ]; then
    append_variable "\"master_instance_type\":\"$CCLOUD_MASTER_INSTANCE_TYPE\""
  fi
  if [ -n "$CCLOUD_WORKER_INSTANCE_TYPE" ]; then
    append_variable "\"worker_instance_type\":\"$CCLOUD_WORKER_INSTANCE_TYPE\""
  fi
  if [[ ${MONSOON_VOLUME_SIZE} && "$MONSOON_VOLUME_SIZE" != 0 ]]; then
    append_variable "\"monsoon_volume_size\":$MONSOON_VOLUME_SIZE"
  fi
  if [[ ${MONSOON_ROOK_VOL} && "$MONSOON_ROOK_VOL" != 0 ]]; then
    append_variable "\"monsoon_rook_vol\":$MONSOON_ROOK_VOL"
  fi
  if [[ ${MONSOON_ROOK_SIZE} && "$MONSOON_ROOK_SIZE" != 0 ]]; then
    append_variable "\"monsoon_rook_size\":$MONSOON_ROOK_SIZE"
  fi
  if [[ ${MONSOON_ROOK_VOLUME_MNT_POINT} && "$MONSOON_ROOK_VOLUME_MNT_POINT" != 0 ]]; then
    append_variable "\"monsoon_rook_volume_mnt_point\":$MONSOON_ROOK_VOLUME_MNT_POINT"
  fi
  if [[ ${CCLOUD_VOLUME_SIZE} && "$CCLOUD_VOLUME_SIZE" != 0 ]]; then
    append_variable "\"ccloud_volume_size\":$CCLOUD_VOLUME_SIZE"
  fi
  if [ -n "$NUMBER_OF_WORKERS" ]; then
    append_variable "\"number_of_workers\":$NUMBER_OF_WORKERS"
  fi
  if [ -n "$MASTER_NAME" ]; then
    append_variable "\"master_name\":\"$MASTER_NAME\""
  fi
  if [ -n "$VOL_TO_EXTEND" ]; then
    append_variable "\"vol_to_extend\":\"$VOL_TO_EXTEND\""
  fi
  if [ -n "$CCLOUD_VOLUME_MNT_POINT" ]; then
    append_variable "\"ccloud_volume_mnt_point\":\"$CCLOUD_VOLUME_MNT_POINT\""
  fi
  if [ -n "$WORKER_NAME_PREFIX" ]; then
    append_variable "\"worker_name_prefix\":\"$WORKER_NAME_PREFIX\""
  fi
  # Parameters for both cluster providers
  if [ -n "$CLUSTER_MANAGER" ]; then
    append_variable "\"cluster_manager\":\"$CLUSTER_MANAGER\""
  fi
  if [ -n "$HDP_STACK_VERSION" ]; then
    parse_version $HDP_STACK_VERSION
    append_variable "\"hdp_stack_versions\":{\"major\":"$VERSION_MAJOR", \"minor\":"$VERSION_MINOR", \"patch\":\""$VERSION_PATCH"\", \"artifact\":\""$VERSION_ARTIFACT"\"}"
    [ -n "$VDF_VERSION" ] && append_variable "\"vdf_version\":\"$VDF_VERSION\""
  fi
  if [ -n "$CDH_STACK_VERSION" ]; then
    parse_version $CDH_STACK_VERSION
    append_variable "\"cdh_stack_version\":{\"major\":"$VERSION_MAJOR", \"minor\":"$VERSION_MINOR"}"
  fi
  if [ -n "$MAPR_STACK_VERSION" ]; then
    append_variable "\"mapr_stack_version\":\"$MAPR_STACK_VERSION\""
    [ -n "$MAPR_ECOSYSTEM_VERSION" ] && append_variable "\"mapr_ecosystem_version\":\"$MAPR_ECOSYSTEM_VERSION\""
  fi
  if [ -n "$USE_KERBEROS" ]; then
    append_variable "\"enable_kerberos\":$USE_KERBEROS"
  fi
  if [ -n "$SPARK_VERSION" ]; then
    parse_version $SPARK_VERSION
    append_variable "\"spark_version\":{\"major\":"$VERSION_MAJOR", \"minor\":"$VERSION_MINOR", \"patch\":"$VERSION_PATCH"}"
  fi
  if [ -n "$EXTERNAL_SPARK_URL" ]; then
    append_variable "\"external_spark_remote_url\":\"$EXTERNAL_SPARK_URL\""
  fi
  if [ -n "$VORA_VERSION" ]; then
    parse_version $VORA_VERSION
    append_variable "\"SAPHanaVora_version\":{\"major\":"$VERSION_MAJOR", \"minor\":"$VERSION_MINOR", \"patch\":"$VERSION_PATCH", \"artifact\":\""$VERSION_ARTIFACT"\"}"
    if [[ ${VERSION_MAJOR} -gt 2103 ]] || ( [[ ${VERSION_MAJOR} -eq 3 ]] && [[ ${VERSION_MINOR} -gt 1 ]]); then
      append_variable "\"enable_client_cert\":\"true\""
    else
      append_variable "\"enable_client_cert\":\"false\""
    fi
  fi
  # if the DI install by SLC Bridge, 
  # then BRIDGE_BUILD_VERSION (build_<infrabox_build_number>) will overwrite the VORA_VERSION
  if [ -n "$BRIDGE_BUILD_VERSION" ]; then
    append_variable "\"vorapkg_version\":\"$BRIDGE_BUILD_VERSION\""
  elif [ -n "$VORA_VERSION" ]; then
    append_variable "\"vorapkg_version\":\"$VORA_VERSION\""
  fi
  if [ -n "$VORA_PACKAGE" ]; then
    append_variable "\"vora_local_pkg\":\"$VORA_PACKAGE\""
    append_variable "\"vora_kubernetes_local_pkg\":\"$VORA_PACKAGE\""
  fi
  if [ -n "$K8S_VERSION" ]; then
    append_variable "\"k8s_version\":\"$K8S_VERSION\""
  fi
  if [ -n "$K8S_INSTALLER_WORKSPACE" ]; then
    append_variable "\"installer_workspace\":\"$K8S_INSTALLER_WORKSPACE\""
  fi
  if [ -n "$K8S_INSTALLER_NAMESPACE" ]; then
    append_variable "\"vora_kube_namespace\":\"$K8S_INSTALLER_NAMESPACE\""
  fi
  if [ -n "$ENABLE_AUTHENTICATION" ]; then
    append_variable "\"enable_authentication\":\"$ENABLE_AUTHENTICATION\""
  fi
  if [ -n "$ENABLE_SECURITY_OPERATOR" ]; then
    append_variable "\"enable_security_operator\":\"$ENABLE_SECURITY_OPERATOR\""
  fi
  # Parameters for dpagent and bdh adapter installation
  if [ -n "$DPAGENT_VERSION" ];then
    append_variable "\"dpagent_version\":\"$DPAGENT_VERSION\""
  fi
  if [ -n "$BDH_ADAPTER_VERSION" ];then
    append_variable "\"bdh_adapter_version\":\"$BDH_ADAPTER_VERSION\""
  fi
  # Parameters for hana xs bdh installation
  if [ -n "$HANA_HOST_NAME" ];then
    append_variable "\"master_name\":\"$HANA_HOST_NAME\""
  fi
  if [ -n "$CCLOUD_HANA_IMAGE" ]; then
    append_variable "\"master_image\":\"$CCLOUD_HANA_IMAGE\""
  fi
  if [ -n "$CCLOUD_HANA_INSTANCE_TYPE" ]; then
    append_variable "\"master_instance_type\":\"$CCLOUD_HANA_INSTANCE_TYPE\""
  fi
  if [ -n "$OUT_OF_CCLOUD_PROJECT" ]; then
    append_variable "\"out_of_ccloud_project\":\"$OUT_OF_CCLOUD_PROJECT\""
  fi
  if [ -n "$HANA_SID" ];then
    append_variable "\"hana_sid\":\"$HANA_SID\""
    append_variable "\"hana_sid_user\":$(echo $HANA_SID| tr '[:upper:]' '[:lower:]')adm"
  fi
  if [ -n "$HANA_SAPADM_USER_PASSWORD" ];then
    append_variable "\"hana_sapadm_user_password\":\"$HANA_SAPADM_USER_PASSWORD\""
  fi
  if [ -n "$HANA_SID_USER_PASSWORD" ];then
    append_variable "\"hana_sid_user_password\":\"$HANA_SID_USER_PASSWORD\""
  fi
  if [ -n "$HANA_DB_SYSTEM_USER_PASSWORD" ];then
    append_variable "\"hana_system_user_password\":\"$HANA_DB_SYSTEM_USER_PASSWORD\""
  fi
  if [ -n "$HANA_XS_ADMIN_PASSWORD" ];then
    append_variable "\"xs_admin_password\":\"$HANA_XS_ADMIN_PASSWORD\""
  fi
  if [ -n "$HANA_VERSION" ];then
    append_variable "\"hana_image_path_wdf\":\"/remote/newdb_archive/NewDB200/rel/20/lcm/linuxx86_64/SAP_HANA_LCM\""
    append_variable "\"xs_component_dirs\":\"/remote/newdb_dev/POOL_EXT/external_components/XSA_RT/SPS11/REL_1_0_63/XSA_RT/linuxx86_64\""
  fi
  if [ -n "$HANA_INST_NUMBER" ];then
    append_variable "\"hana_inst_number\":\"$HANA_INST_NUMBER\""
  fi
  if [ -n "$HANA_IMAGE_PATH" ];then
    append_variable "\"hana_image_path\":\"$HANA_IMAGE_PATH\""
  fi
  if [ -n "$HANA_IMAGE_NAME" ];then
    append_variable "\"hana_image_name\":\"$HANA_IMAGE_NAME\""
  fi
  if [ -n "$HANA_TESTPACK_PATH" ];then
    append_variable "\"hana_testpack_image_path\":\"$HANA_TESTPACK_PATH\""
  fi
  if [ -n "$HANA_TESTPACK_NAME" ];then
    append_variable "\"hana_testpack_image_name\":\"$HANA_TESTPACK_NAME\""
  fi
  if [ -n "$HANA_ADD_ONS" ];then
    append_variable "\"hana_add_ons\":\"$HANA_ADD_ONS\""
  fi
  if [ -n "$URL_ADMIN_PACKAGE" ];then
    append_variable "\"url_admin_package\":\"$URL_ADMIN_PACKAGE\""
  fi
  if [ -n "$URL_JOBSCHEDULER_PACKAGE" ];then
    append_variable "\"url_jobscheduler_package\":\"$URL_JOBSCHEDULER_PACKAGE\""
  fi
  if [ -n "$URL_SAPUI5_PACKAGE" ];then
    append_variable "\"url_sapui5_package\":\"$URL_SAPUI5_PACKAGE\""
  fi
  if [ -n "$URL_HRTT_PACKAGE" ];then
    append_variable "\"url_hrtt_package\":\"$URL_HRTT_PACKAGE\""
  fi
  if [ -n "$URL_WEBIDE_PACKAGE" ];then
    append_variable "\"url_webide_package\":\"$URL_WEBIDE_PACKAGE\""
  fi
  if [ -n "$URL_BDH_ASSEMBLY_PACKAGE" ];then
    append_variable "\"url_bdh_assembly_package\":\"$URL_BDH_ASSEMBLY_PACKAGE\""
  fi
  if [ -n "$VORA_INSTALL_TEXTANALYSIS" ];then
    append_variable "\"vora_install_textanalysis\":\"$VORA_INSTALL_TEXTANALYSIS\""
  fi
  if [ -n "$EMAIL" ];then
    append_variable "\"user_email\":\"$(echo ${EMAIL%%,*})\""
  fi
  if [ -n "$PROJECT_NAME" ];then
    append_variable "\"project_name\":\"$PROJECT_NAME\""
  fi
  if [ -n "$OUT_OF_CCLOUD_PROJECT" ];then
    append_variable "\"out_of_ccloud_project\":\"${OUT_OF_CCLOUD_PROJECT}\""
  fi
  if [ -n "$SHOOT_NAME" ];then
    append_variable "\"gardener_shoot_name\":\"$SHOOT_NAME\""
  fi
  if [ -n "$IP_SUBNET" ];then
    append_variable "\"gardener_ip_subnet\":\"$IP_SUBNET\""
  fi
  if [ -n "$AWS_MACHINE_TYPE" ];then
    append_variable "\"gardener_aws_machine_type\":\"$AWS_MACHINE_TYPE\""
  fi
  if [ -n "$AWS_REGION" ];then
    append_variable "\"gardener_aws_region\":\"$AWS_REGION\""
  fi
  if [ -n "$AWS_VOLUME_SIZE" ];then
    append_variable "\"gardener_aws_volume_size\":\"$AWS_VOLUME_SIZE\""
  fi
  if [ -n "$GARDENER_AWS_K8S_CLUSTER_NAME" ];then
    append_variable "\"gardener_aws_k8s_cluster_name\":\"$GARDENER_AWS_K8S_CLUSTER_NAME\""
  fi
  if [ -n "$GARDENER_SHOOT_NAME" ];then
    append_variable "\"gardener_shoot_name\":\"$GARDENER_SHOOT_NAME\""
  fi
  if [ -n "$GCP_PROJECT_ID" ];then
    append_variable "\"gcloud_project_id\":\"$GCP_PROJECT_ID\""
  fi
  if [ -n "$GCP_DOCKER_REGISTRY_SUFFIX" ];then
    append_variable "\"gcloud_docker_registry_suffix\":\"$GCP_DOCKER_REGISTRY_SUFFIX\""
  fi
  if [ -n "$GKE_K8S_CLUSTER_NAME" ];then
    append_variable "\"gcloud_k8s_cluster_name\":\"$GKE_K8S_CLUSTER_NAME\""
  fi
  if [ -n "$GKE_K8S_VPC" ];then
    append_variable "\"gcloud_k8s_vpc\":\"$GKE_K8S_VPC\""
  fi
  if [ -n "$GCLOUD_K8S_SUBNETWORK" ];then
    append_variable "\"gcloud_k8s_subnetwork\":\"$GCLOUD_K8S_SUBNETWORK\""
  fi
  if [ -n "$GKE_EXPOSE_INGRESS_AT_ROUTE53" ];then
    append_variable "\"gke_expose_ingress_at_route53\":\"$GKE_EXPOSE_INGRESS_AT_ROUTE53\""
  fi
  if [ -n "$GCP_REGION" ];then
    append_variable "\"gcloud_region\":\"$GCP_REGION\""
  fi
  if [ -n "$GCP_ZONE" ];then
    append_variable "\"gcloud_zone\":\"$GCP_ZONE\""
  fi
  if [ -n "$GCP_HANA_INSTANCE_NAME" ];then
    append_variable "\"gcloud_instance_master_name\":\"$GCP_HANA_INSTANCE_NAME\""
  fi
  if [ -n "$GCP_INSTANCE_NAME" ];then
    append_variable "\"gcloud_instance_name\":\"$GCP_INSTANCE_NAME\""
  fi
  if [ -n "$GCP_MACHINE_TYPE" ];then
    append_variable "\"gcloud_k8s_cluster_node_machine_type\":\"$GCP_MACHINE_TYPE\""
  fi
  if [ -n "$GCP_INSTANCE_TYPE" ];then
    append_variable "\"gcloud_instance_machine_type\":\"$GCP_INSTANCE_TYPE\""
  fi
  if [ -n "$GCP_INSTANCE_IMAGE_FAMILY" ];then
    append_variable "\"gcloud_image_family\":\"$GCP_INSTANCE_IMAGE_FAMILY\""
  fi
  if [ -n "$GCP_INSTANCE_IMAGE" ];then
    append_variable "\"gcloud_instance_image_type\":\"$GCP_INSTANCE_IMAGE\""
  fi
  if [ -n "$GCP_IMAGE_TYPE" ];then
    append_variable "\"gcloud_k8s_cluster_node_image_type\":\"$GCP_IMAGE_TYPE\""
  fi
  if [ -n "$GCP_NODE_VOLUME_SIZE" ];then
    append_variable "\"gcloud_k8s_cluster_node_disk_size\":\"$GCP_NODE_VOLUME_SIZE\""
  fi
  if [ -n "$GCP_APPLICATION_CREDENTIALS" ];then
    append_variable "\"google_application_credentials\":\"$GCP_APPLICATION_CREDENTIALS\""
  fi
  if [ -n "$CLOUD_PLATFORM" ];then
    append_variable "\"cloud_platform\":\"$CLOUD_PLATFORM\""
  fi
  if [ -n "$VSYSTEM_VERSION" ];then
    append_variable "\"vsystem_pkg_version\":\"$VSYSTEM_VERSION\""
  fi
  if [ -n "$AZURE_SUBSCRIPTION_ID" ];then
    append_variable "\"subscription_id\":\"$AZURE_SUBSCRIPTION_ID\""
  fi
  if [ -n "$AZURE_CLIENT_ID" ];then
    append_variable "\"client_id\":\"$AZURE_CLIENT_ID\""
  fi
  if [ -n "$AZURE_CLIENT_SECRET" ];then
    append_variable "\"client_secret\":\"$AZURE_CLIENT_SECRET\""
  fi
  if [ -n "$AZURE_TENANT" ];then
    append_variable "\"tenant\":\"$AZURE_TENANT\""
  fi
  if [ -n "$AZURE_MASTER_INSTANCE_TYPE" ]; then
    append_variable "\"master_instance_type\":\"$AZURE_MASTER_INSTANCE_TYPE\""
  fi
  if [ -n "$AZURE_WORKER_INSTANCE_TYPE" ]; then
    append_variable "\"worker_instance_type\":\"$AZURE_WORKER_INSTANCE_TYPE\""
  fi
  if [ -n "$AZURE_K8S_CLUSTER_NAME" ];then
    append_variable "\"azure_k8s_cluster_name\":\"$AZURE_K8S_CLUSTER_NAME\""
  fi
  if [ -n "$SKIP_VSYSTEM_ASSEMBLY" ]; then
    append_variable "\"skip_vsystem_assembly\":\"$SKIP_VSYSTEM_ASSEMBLY\""
  fi
  if [ -n "$AZURE_RESOURCE_GROUP" ]; then
    append_variable "\"azure_resource_group\":\"$AZURE_RESOURCE_GROUP\""
  fi
  if [ -n "$AZURE_REGISTRY_NAME" ]; then
    append_variable "\"azure_registry_name\":\"$AZURE_REGISTRY_NAME\""
  fi
  if [ -n "$AKS_CLUSTER_NAME" ]; then
    append_variable "\"aks_cluster_name\":\"$AKS_CLUSTER_NAME\""
  fi
  if [ -n "$AZURE_RESOURCE_LOCATION" ]; then
    append_variable "\"azure_resource_location\":\"$AZURE_RESOURCE_LOCATION\""
  fi
  if [ -n "$AKS_NODE_DISKSIZE" ]; then
    append_variable "\"aks_node_disksize\":\"$AKS_NODE_DISKSIZE\""
  fi
  if [ -n "$AKS_FAST_DEPLOY" ]; then
    append_variable "\"aks_fast_deploy\":\"$AKS_FAST_DEPLOY\""
  fi
  if [ -n "$GKE_K8S_CLUSTER_KUBECONFIG" ]; then
    append_variable "\"gke_k8s_cluster_kubeconfig\":\"$GKE_K8S_CLUSTER_KUBECONFIG\""
  fi
  if [ -n "$KUBE_ADMIN_CONFIG_PATH" ]; then
    append_variable "\"kube_admin_config_path\":\"$KUBE_ADMIN_CONFIG_PATH\""
  fi
  if [ -n "$KOPS_VPC" ]; then
    append_variable "\"kops_vpc\":\"$KOPS_VPC\""
  fi
  if [ -n "$KOPS_SUBNET_PREFIX" ]; then
    append_variable "\"subnet_prefix\":\"$KOPS_SUBNET_PREFIX\""
  fi
  if [ -n "$KOPS_MASTER_INSTANCE_TYPE" ]; then
    append_variable "\"master_instance_type\":\"$KOPS_MASTER_INSTANCE_TYPE\""
  fi
  if [ -n "$KOPS_WORKER_INSTANCE_TYPE" ]; then
    append_variable "\"worker_instance_type\":\"$KOPS_WORKER_INSTANCE_TYPE\""
  fi
  if [ -n "$EKS_NODE_INSTANCE_TYPE" ]; then
    append_variable "\"eks_node_instance_type\":\"$EKS_NODE_INSTANCE_TYPE\""
  fi
  if [ -n "$BDH_INSTALL_PREFLIGHT_CHECKS" ]; then
    append_variable "\"bdh_install_preflight_checks\":\"$BDH_INSTALL_PREFLIGHT_CHECKS\""
  fi
  if [ -n "$BDH_ONE_NODE_INSTALLATION" ]; then
    append_variable "\"bdh_one_node_installation\":\"$BDH_ONE_NODE_INSTALLATION\""
  fi
  if [ -n "$KOPS_VOLUME_SIZE" ]; then
    append_variable "\"aws_volume_size\":\"$KOPS_VOLUME_SIZE\""
  fi
  if [ -n "$KOPS_K8S_CLUSTER_NAME" ]; then
    append_variable "\"kops_k8s_cluster_name\":\"$KOPS_K8S_CLUSTER_NAME\""
  fi
  if [ -n "$EKS_K8S_CLUSTER_NAME" ]; then
    append_variable "\"eks_k8s_cluster_name\":\"$EKS_K8S_CLUSTER_NAME\""
  fi
  if [ -n "$AZURE_KUBECONFIG" ]; then
    append_variable "\"azure_kubeconfig\":\"$AZURE_KUBECONFIG\""
  fi
  if [ -n "$KOPS_AWS_REGION" ]; then
    append_variable "\"kops_aws_region\":\"$KOPS_AWS_REGION\""
  fi
  if [ -n "$KOPS_AWS_ZONES" ]; then
    append_variable "\"kops_aws_zones\":\"$KOPS_AWS_ZONES\""
  fi
  if [ -n "$EKS_AWS_REGION" ]; then
    append_variable "\"eks_aws_region\":\"$EKS_AWS_REGION\""
  fi
  if [ -n "$DOCKER_ARTIFACTORY" ]; then
    append_variable "\"docker_artifactory\":\"$DOCKER_ARTIFACTORY\""
  fi
  if [ -n "$ARTIFACTORY_LOGIN_OPT" ]; then
    append_variable "\"artifactory_login_opt\":\"$ARTIFACTORY_LOGIN_OPT\""
  fi
  if [ -n "$ARTIFACTORY_LOGIN_USERNAME" ]; then
    append_variable "\"artifactory_login_username\":\"$ARTIFACTORY_LOGIN_USERNAME\""
  fi
  if [ -n "$ARTIFACTORY_LOGIN_PASSWORD" ]; then
    append_variable "\"artifactory_login_password\":\"$ARTIFACTORY_LOGIN_PASSWORD\""
  fi
  if [ -n "$SAP_DH_BIN_LEVEL" ]; then
    append_variable "\"sap_dh_bin_level\":\"$SAP_DH_BIN_LEVEL\""
  fi
  if [ -n "$VORA_KUBE_PREFIX_URL" ]; then
    append_variable "\"vora_kube_prefix_url\":\"$VORA_KUBE_PREFIX_URL\""
  fi
  if [ -n "$ENABLE_STORAGE_CHECKPOINT" ]; then
    append_variable "\"enable_storage_checkpoint\":\"$ENABLE_STORAGE_CHECKPOINT\""
  fi
  if [ -n "$GKE_BUCKET_NAME" ]; then
    append_variable "\"gke_bucket_name\":\"$GKE_BUCKET_NAME\""
  fi
  if [ -n "$KOPS_K8S_CLUSTER_KUBECONFIG" ]; then
    append_variable "\"kops_k8s_cluster_kubeconfig\":\"$KOPS_K8S_CLUSTER_KUBECONFIG\""
  fi
  if [ -n "$EKS_K8S_CLUSTER_KUBECONFIG" ]; then
    append_variable "\"eks_k8s_cluster_kubeconfig\":\"$EKS_K8S_CLUSTER_KUBECONFIG\""
  fi
  if [ -n "$EKS_AWS_REGION" ]; then
    append_variable "\"eks_aws_region\":\"$EKS_AWS_REGION\""
  fi
  if [ -n "$GARDENER_SHOOT_KUBECONFIG" ]; then
    append_variable "\"gardener_shoot_kubeconfig\":\"$GARDENER_SHOOT_KUBECONFIG\""
  fi
  if [ -n "$GARDENER_AWS_REGION" ]; then
    append_variable "\"gardener_aws_region\":\"$GARDENER_AWS_REGION\""
  fi
 
  if [ -n "$VSYSTEM_USE_EXTERNAL_AUTH" ]; then
    append_variable "\"vsystem_use_external_auth\":\"$VSYSTEM_USE_EXTERNAL_AUTH\""
  fi

  if [ -n "$ENABLE_NETWORK_POLICIES" ]; then
    append_variable "\"enable_network_policies\":\"$ENABLE_NETWORK_POLICIES\""
  fi

  if [ -z "${ANSIBLE_DEBUG}" ]; then
    ANSIBLE_DEBUG="-v"
  fi
  if [ -n "$BUCKET_DATA_PATH" ]; then
    append_variable "\"bucket_data_path\":\"$BUCKET_DATA_PATH\""
  fi
  if [ -n "$EXPOSE_VSYSTEM" ]; then
    append_variable "\"expose_vsystem\":\"$EXPOSE_VSYSTEM\""
  fi
  if [ -n "$EXPOSE_VORA_TXC" ]; then
    append_variable "\"expose_vora_txc\":\"$EXPOSE_VORA_TXC\""
  fi
  if [ -n "$EXPOSE_TEXT_ANALYSIS" ]; then
    append_variable "\"expose_text-analysis\":\"$EXPOSE_TEXT_ANALYSIS\""
  fi
  if [ -n "$DEV_CONFIG_FILE" ]; then
    append_variable "\"dev_config_file\":\"$DEV_CONFIG_FILE\""
  fi
  if [ -n "$HANA_RESOURCES_REQUESTS_MEMORY" ]; then
    append_variable "\"hana_resources_requests_memory\":\"$HANA_RESOURCES_REQUESTS_MEMORY\""
  fi
  if [ -n "$HANA_RESOURCES_LIMITS_MEMORY" ]; then
    append_variable "\"hana_resources_limits_memory\":\"$HANA_RESOURCES_LIMITS_MEMORY\""
  fi
  if [ -n "$VORA_PASSWORD" ]; then
    append_variable "\"vora_password\":\"$VORA_PASSWORD\""
  fi
  if [ -n "$VORA_SYSTEM_TENANT_PASSWORD" ]; then
    append_variable "\"vora_system_tenant_password\":\"$VORA_SYSTEM_TENANT_PASSWORD\""
  fi
  if [ -n "$INSTALL_VORA_VIA_SLPLUGIN" ]; then
    append_variable "\"install_vora_via_slplugin\":\"$INSTALL_VORA_VIA_SLPLUGIN\""
  fi
  if [ -n "$UNINSTALL_VIA_SLCB" ]; then
    append_variable "\"uninstall_via_slcb\":\"$UNINSTALL_VIA_SLCB\""
  fi  
  if [ -n "$INSTALL_VIA_SLCB" ]; then
    append_variable "\"install_via_slcb\":\"$INSTALL_VIA_SLCB\""
  fi
  if [ -n "$EXTRA_INSTALL_PARAMETERS" ]; then
    append_variable "\"extra_install_parameters\":\"$EXTRA_INSTALL_PARAMETERS\""
  fi
  if [ -n "$GKE_CHANGE_INGRESS_TIMEOUT" ]; then
    append_variable "\"gke_change_ingress_timeout\":\"$GKE_CHANGE_INGRESS_TIMEOUT\""
  fi
  if [ -n "$GKE_INGRESS_TIMEOUT" ]; then
    append_variable "\"gke_ingress_timeout\":\"$GKE_INGRESS_TIMEOUT\""
  fi
  if [ -n "$ENABLE_KANIKO" ]; then
    append_variable "\"enable_kaniko\":\"$ENABLE_KANIKO\""
  fi
  if [ -n "$VORA_KUBE_SUFFIX" ]; then
    append_variable "\"vora_kube_suffix\":\"$VORA_KUBE_SUFFIX\""
  fi
  if [ -n "$OFFLINE_INSTALL" ]; then
    append_variable "\"offline_install\":\"$OFFLINE_INSTALL\""
  fi
  if [ -n "$AKS_SUBSCRIPTION_NAME" ]; then
    append_variable "\"subscription_id\":\"$AKS_SUBSCRIPTION_NAME\""
  fi
  if [ -n "$AZURE_VFLOW_REGISTRY_NAME" ]; then
    append_variable "\"azure_vflow_registry_name\":\"$AZURE_VFLOW_REGISTRY_NAME\""
  fi
  if [ -n "$AZURE_VFLOW_RESOURCE_GROUP" ]; then
    append_variable "\"azure_vflow_resource_group\":\"$AZURE_VFLOW_RESOURCE_GROUP\""
  fi
  if [ -n "$GCP_VFLOW_DOCKER_REGISTRY_SUFFIX" ]; then
    append_variable "\"gcp_vflow_docker_registry_suffix\":\"$GCP_VFLOW_DOCKER_REGISTRY_SUFFIX\""
  fi
  if [ -n "$EKS_DOCKER_REGISTRY_SUFFIX" ]; then
    append_variable "\"eks_docker_registry_suffix\":\"$EKS_DOCKER_REGISTRY_SUFFIX\""
  fi
  if [ -n "$EKS_VFLOW_DOCKER_REGISTRY_SUFFIX" ]; then
    append_variable "\"eks_vflow_docker_registry_suffix\":\"$EKS_VFLOW_DOCKER_REGISTRY_SUFFIX\""
  fi
  if [ -n "$ENABLE_BACKUP" ]; then
    append_variable "\"enable_backup\":\"$ENABLE_BACKUP\""
  fi
  if [ -n "$ENABLE_RESTORE" ]; then
    append_variable "\"enable_restore\":\"$ENABLE_RESTORE\""
  fi
  if [ -n "$DI_BACKUP_NAME" ]; then
    append_variable "\"di_backup_name\":\"$DI_BACKUP_NAME\""
  fi
  if [ -n "$USE_CUSTOMIZED_SLCB_BINARY" ]; then
    append_variable "\"use_customized_slcb_binary\":\"$USE_CUSTOMIZED_SLCB_BINARY\""
  fi
  if [ -n "$INSTALLER_VALIDATION" ]; then
    append_variable "\"installer_validation\":\"$INSTALLER_VALIDATION\""
  fi
  if [ -n "$AZURE_DOCKER_LOGIN_USERNAME" ]; then
    append_variable "\"azure_docker_login_username\":\"$AZURE_DOCKER_LOGIN_USERNAME\""
  fi
  if [ -n "$AZURE_DOCKER_LOGIN_ADDRESS" ]; then
    append_variable "\"azure_docker_login_address\":\"$AZURE_DOCKER_LOGIN_ADDRESS\""
    append_variable "\"aks_docker_install_registry\":\"$AZURE_DOCKER_LOGIN_ADDRESS\""
  fi
  if [ -n "$AZURE_DOCKER_LOGIN_PASSWORD" ]; then
    append_variable "\"azure_docker_login_password\":\"$AZURE_DOCKER_LOGIN_PASSWORD\""
  fi
  # the BASE_PROFILE will has three kinds of valur, di-platform-full, di-platform-extended, di-platform
  # di-platform is basic DI, di-platform-extended is basic DI + diagnostics, di-platform-full is basic DI + diagnostics + VORA Tools
  if [ -n "$BASE_PROFILE" ]; then
    append_variable "\"base_profile\":\"$BASE_PROFILE\""
    append_variable "\"product_bridge_name\":\"com.sap.datahub.linuxx86_64/${BASE_PROFILE}-product-bridge\""
  fi
  # comment out the SLCB_VERSION since the 1.1.38,1.1.40,1.1.42 are not compatible with ansible code
  # must use fix version
  if [ -n "$SLCB_VERSION" ]; then
    append_variable "\"slcb_version\":\"$SLCB_VERSION\""
    if [[ "$SLCB_VERSION" < "1.1.82" ]]; then
      append_variable "\"slcb_package_suffix\":\"exe\""
    fi
  fi
  if [ -n "$EKS_AWS_S3_BUCKET_NAME" ]; then
    append_variable "\"eks_aws_s3_bucket_name\":\"$EKS_AWS_S3_BUCKET_NAME\""
  fi
  if [ -n "$GITHUB_BASE_URL" ]; then
    append_variable "\"github_base_url\":\"$GITHUB_BASE_URL\""
  fi
  if [ -n "$AUTH_HEADER" ]; then
    append_variable "\"im_auth_header\":\"${AUTH_HEADER#*Bearer }\""
  fi
  if [ -n "$VORA_SYSTEM_TENANT_PASSWORD" ]; then
    append_variable "\"vora_system_tenant_password\":\"${VORA_SYSTEM_TENANT_PASSWORD}\""
  fi
  if [ -n "$VORA_PASSWORD" ]; then
    append_variable "\"vora_password\":\"${VORA_PASSWORD}\""
  fi
  # Now deploy the cluster
  echo "$deploy_cmd ${ANSIBLE_DEBUG}"
  eval "$deploy_cmd ${ANSIBLE_DEBUG}"

  if [ $? -eq 0 ];then
      return 0
  else
      return 1
  fi
}
#this function be add for doing some cleanup with run one ansible playbook
#2 arguments needed , firstly is inventory file , second playbook file
cleanup()
{
  if [ -f ${ROOT_DIR}/playbooks/vora/vora_installation.log ];then
    cp ${ROOT_DIR}/playbooks/vora/vora_installation.log  ${OUTPUT_DIR}/vora_installation.log
  fi
  inventory_file=${1}
  playbook=${2}
  ms_placeholder_cnt=0
  ms_placeholder_cnt=`cat ${inventory_file} |grep "xxx.mo.sap.corp" |wc -l`
  cat ${inventory_file}
  if [ ${ms_placeholder_cnt} -eq 0 ];then
    echo "Start cleanup ..."
    bootstrap_cluster_on_demand "ansible-playbook -i ${inventory_file} ${playbook}"
    echo "Done cleanup ...."
  else
    echo "No monsoon instances be created , no cleanup needed !"
  fi
}

