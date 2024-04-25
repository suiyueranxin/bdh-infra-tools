#!/usr/bin/env bash
# © 2022 SAP SE or an SAP affiliate company. All rights reserved.

export KUBECONFIG=/tmp/admin.conf
export OUT_DIR=/infrabox/upload/archive

HELM2=helm
HELM3=helm3
debug_sh_error_file=debug_sh_errors.log

preflight() {
echo " ########################################################"
echo " ### Data Intelligence Diagnostic Info Collector v0.1 ###"
echo " ########################################################"

if ! command -v kubectl &> /dev/null ; then
  echo "command kubectl could not be found"; exit 1
fi


current_context_ns=$(kubectl config view --minify --output 'jsonpath={..namespace}')
if [ -z "$NAMESPACE" ] ; then
  if [ -n "$current_context_ns" ]; then
    export NAMESPACE="$current_context_ns"
    echo "Using namespace $current_context_ns from current context.";
  else
    export NAMESPACE=datahub
    echo 'NAMESPACE is empty, defaulting to datahub';
  fi
fi

if ! kubectl get ns; then
  echo 'USER cannot list resource "namespaces" in API group "" at the cluster scope'
else
  if ! kubectl get namespace "${NAMESPACE}"; then
    echo "namespace ${NAMESPACE} does not exist!"; exit 1
  fi
fi

if ! get_helm3_cmd ; then
  echo "[warn] helm3 client not found";
fi

if ! get_helm2_cmd ; then
  echo "[info] helm2 client not found. Will skip helm2 dump"
fi
}

get_helm3_cmd(){
if helm3 version --short --client 2>> "/dev/null" | grep "v3\."; then
  HELM3=helm3
elif helm version --short --client 2>> "/dev/null" | grep "v3\."; then
  HELM3=helm
elif helmv3 version --short --client 2>> "/dev/null" | grep "v3\."; then
  HELM3=helmv3
else
  HELM3=""
  return 1
fi

echo "Helm3 version:" "$(${HELM3} version 2>> $diagnostic_dir/$debug_sh_error_file)"
}

get_helm2_cmd(){
    if helm2 version --short --client 2>> "/dev/null" | grep "v2\."; then
      HELM2=helm2
    elif helm version --short --client 2>> "/dev/null" | grep "v2\."; then
      HELM2=helm
    elif helmv2 version --short --client 2>> "/dev/null" | grep "v2\."; then
      HELM2=helmv2
    else
      HELM2=""
      return 1
    fi

    echo "Helm2 version: $("HELM2" version)"
}

### PREFLIGHT ###
preflight

diagnostic_dir_name=di_diagnostic-$(date '+%s')
diagnostic_dir=/tmp/${diagnostic_dir_name}
mkdir -p "$diagnostic_dir"

kubectl version > "${diagnostic_dir}/kubectl_version" 2>> "$diagnostic_dir/$debug_sh_error_file"

### Helm2 dump ###
if [ -n "$HELM2" ] ; then
  ${HELM2} version > "${diagnostic_dir}/helm_version" 2>> "$diagnostic_dir/$debug_sh_error_file"
  mkdir -p "$diagnostic_dir/helm_v2_dump"
  echo "Listing helm v2 releases..."
  ${HELM2} ls -a --tiller-namespace datahub-system > "$diagnostic_dir/helm_v2_dump/helm_v2_ls.yaml" 2>> "$diagnostic_dir/$debug_sh_error_file"
  echo "Getting helm v2 histories and statuses..."
  mkdir -p "$diagnostic_dir/helm_v2_dump/helm_v2_histories"
  mkdir -p "$diagnostic_dir/helm_v2_dump/helm_v2_statuses"
  helm_releases=( $(${HELM2} ls -a -q --tiller-namespace datahub-system 2>> "$diagnostic_dir/$debug_sh_error_file") )

  for helm_release in "${helm_releases[@]}"
  do
    ${HELM2} history "${helm_release}" --tiller-namespace datahub-system -o yaml > "$diagnostic_dir/helm_v2_dump/helm_v2_histories/${helm_release}.yaml" 2>> "$diagnostic_dir/$debug_sh_error_file"
    ${HELM2} status  "${helm_release}" --tiller-namespace datahub-system -o yaml > "$diagnostic_dir/helm_v2_dump/helm_v2_statuses/${helm_release}.yaml" 2>> "$diagnostic_dir/$debug_sh_error_file"
  done
fi

### Helm3 dump ###
if [ -n "$HELM3" ] ; then
  ${HELM3} version > "${diagnostic_dir}/helm3_version" 2>> "$diagnostic_dir/$debug_sh_error_file"
  mkdir -p "$diagnostic_dir/helm_v3_dump"
  echo "Listing helm v3 releases..."
  ${HELM3} ls -a -A > "$diagnostic_dir/helm_v3_dump/helm_v3_ls.yaml" 2>> "$diagnostic_dir/$debug_sh_error_file"
  echo "Getting helm v3 histories and statuses..."
  helm_v3_releases=( $(${HELM3} ls -a -A -q -n "${NAMESPACE}" 2>> "$diagnostic_dir/$debug_sh_error_file") )

  for helm_v3_release in "${helm_v3_releases[@]}"
  do
    {
    ${HELM3} get values "${helm_v3_release}" -a -n "${NAMESPACE}"> "$diagnostic_dir/helm_v3_dump/${helm_v3_release}_values";
    ${HELM3} get values "${helm_v3_release}" -a -n "${NAMESPACE}" -o yaml > "$diagnostic_dir/helm_v3_dump/${helm_v3_release}_values.yaml";
    ${HELM3} get manifest "${helm_v3_release}" -n "${NAMESPACE}" > "$diagnostic_dir/helm_v3_dump/${helm_v3_release}_manifest";
    ${HELM3} get hooks "${helm_v3_release}" -n "${NAMESPACE}" > "$diagnostic_dir/helm_v3_dump/${helm_v3_release}_hooks";
    ${HELM3} get all "${helm_v3_release}" -n "${NAMESPACE}" > "$diagnostic_dir/helm_v3_dump/${helm_v3_release}_all_info";
    ${HELM3} history "${helm_v3_release}" -n "${NAMESPACE}" > "$diagnostic_dir/helm_v3_dump/${helm_v3_release}_history";
    ${HELM3} history "${helm_v3_release}" -n "${NAMESPACE}" -o yaml > "$diagnostic_dir/helm_v3_dump/${helm_v3_release}_history.yaml";
    ${HELM3} status "${helm_v3_release}" -n "${NAMESPACE}" > "$diagnostic_dir/helm_v3_dump/${helm_v3_release}_status";
    ${HELM3} status "${helm_v3_release}" -n "${NAMESPACE}" -o yaml > "$diagnostic_dir/helm_v3_dump/${helm_v3_release}_status.yaml";
    } 2>> "$diagnostic_dir/$debug_sh_error_file"
  done
fi

### EVENTS ###
echo "Getting events..."
kubectl get events --sort-by='.lastTimestamp' -o yaml -n "${NAMESPACE}" > "$diagnostic_dir/events.yaml"

### Installer CRs ###
echo "Getting installer resources..."
mkdir -p "$diagnostic_dir/installer_resources"
mkdir -p "$diagnostic_dir/installer_resources/helmdeployments"

echo "Listing Data Intelligence k8s API resources..."
installer_resources=( $(kubectl -n "${NAMESPACE}" api-resources --api-group="installers.datahub.sap.com" -o name) )
vsystem_resources=( $(kubectl -n "${NAMESPACE}" api-resources --api-group="vsystem.datahub.sap.com" -o name) )
layer1_helmdeployments=( $(kubectl -n "${NAMESPACE}" get helmdeployments.installers.datahub.sap.com --no-headers -o=custom-columns='NAME:.metadata.name'))

echo "Saving installer CRs..."
for installer_resource in "${installer_resources[@]}"
do
  kubectl get "${installer_resource}" -o yaml -n "${NAMESPACE}" >> "$diagnostic_dir/installer_resources/${installer_resource}.yaml"
done

echo "Saving vSystem CRs..."
for vsystem_resource in "${vsystem_resources[@]}"
do
  kubectl get "${vsystem_resource}" -o yaml -n "${NAMESPACE}" >> "$diagnostic_dir/installer_resources/${vsystem_resource}.yaml"
done
echo "Saving Vora CR..."
kubectl get voraclusters.sap.com -o yaml -n "${NAMESPACE}" >> "$diagnostic_dir/installer_resources/voraclusters.sap.com.yaml"

echo "Saving Layer1 HelmDeployment CRs..."
for layer1_helmdeployment in "${layer1_helmdeployments[@]}"
do
  kubectl get helmdeployments.installers.datahub.sap.com "${layer1_helmdeployment}" -o yaml -n "${NAMESPACE}" >> "$diagnostic_dir/installer_resources/helmdeployments/${layer1_helmdeployment}.yaml"
done

echo "Saving k8s resources..."
mkdir -p "$diagnostic_dir/k8s_resources"
mkdir -p "$diagnostic_dir/k8s_resources/summary"
## exclude secrets and resources that are already collected
k8s_resources=( $(kubectl api-resources -o name | grep -v -e "installers.datahub.sap.com" -e "vsystem.datahub.sap.com" -e "sap.com" -e "velero.io" -e "projectcalico.org" -e "secrets") )
for k8s_resource in "${k8s_resources[@]}"
do
  kubectl get "${k8s_resource}" -o wide -n "${NAMESPACE}" >> "$diagnostic_dir/k8s_resources/summary/${k8s_resource}_summary.txt" 2>> "$diagnostic_dir/$debug_sh_error_file"
  kubectl get "${k8s_resource}" -o yaml -n "${NAMESPACE}" >> "$diagnostic_dir/k8s_resources/${k8s_resource}.yaml" 2>> "$diagnostic_dir/$debug_sh_error_file"
done
## only get secret names list, exclude content
kubectl get secrets -o wide -n "${NAMESPACE}" >> "$diagnostic_dir/k8s_resources/summary/secrets_summary.txt" 2>> "$diagnostic_dir/$debug_sh_error_file"

mkdir -p "$diagnostic_dir/dhinstaller_diag"
{
kubectl exec -it -n datahub-system datahub-operator-0 -- dhinstaller version > "$diagnostic_dir/dhinstaller_diag/dhinstaller_version"
kubectl exec -it -n datahub-system datahub-operator-0 -- dhinstaller dependency tree --ignore-completed=false -n "${NAMESPACE}" > "$diagnostic_dir/dhinstaller_diag/dependency_tree"
echo "***** SUGGESTED TAB/INDENTATION SIZE IS 8 *****" > "$diagnostic_dir/dhinstaller_diag/dependency_tree_verbose"
kubectl exec -it -n datahub-system datahub-operator-0 -- dhinstaller dependency tree --ignore-completed=false -n "${NAMESPACE}" -v >> "$diagnostic_dir/dhinstaller_diag/dependency_tree_verbose"
} 2>> "$diagnostic_dir/$debug_sh_error_file"
echo "Getting cluster-info dump..."
mkdir -p "${diagnostic_dir}/cluster-dump"
kubectl cluster-info dump \
    --output-directory="${diagnostic_dir}/cluster-dump" \
    --all-namespaces


echo "Compress log files to improve performance"
tar -czf "${diagnostic_dir}.tar.gz" -C /tmp "${diagnostic_dir_name}" \
    && rm -rf "${diagnostic_dir}"

mv "${diagnostic_dir}.tar.gz" "${OUT_DIR}"

echo "Archive that contains the diagnostic information was created successfully."
echo "Path: ${OUT_DIR}/${diagnostic_dir_name}.tar.gz"
