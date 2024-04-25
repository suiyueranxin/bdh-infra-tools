#!/bin/bash

# to get cluster name. example:
# export K8S_CLUSTER_NAMES='1-gke:sap-bdh-infra-20211115-031612542,2-gke:sap-bdh-infra-20211115-031606426,3-gke:sap-bdh-infra-20211115-031602651,4-gke:sap-bdh-infra-20211115-031612663'
# export K8S_CLUSTER_NAMES='dhaas_aws:sap-bdh-infra-20211115-023421075'
  if [ -n "${K8S_CREATION_JOB}" ]; then
    OLD_IFS="$IFS" 
    IFS="," 
    arr=(${K8S_CREATION_JOB}) 
    IFS="$OLD_IFS" 
    for creation_job in ${arr[@]} 
    do
      if [[ -f /infrabox/inputs/${creation_job}/bdh_base_version.sh ]]; then
        source /infrabox/inputs/${creation_job}/bdh_base_version.sh
      fi
      if [[ -f /infrabox/inputs/${creation_job}/k8s_cluster.txt ]]; then
        if [[ "${creation_job}" == dhaas* ]]; then
          cluster_name_item=$(echo $creation_job |rev |cut -d '_' -f2 |rev)_$(echo $creation_job |rev |cut -d '_' -f1 |rev):$(cat /infrabox/inputs/${creation_job}/k8s_cluster.txt)
        else
          cluster_name_item=$(echo $creation_job |rev |cut -d '_' -f1 |rev):$(cat /infrabox/inputs/${creation_job}/k8s_cluster.txt)
        fi
        if [ -n "${k8s_clusters}" ] && [ -n "${cluster_name_item}" ]; then
          k8s_clusters=${k8s_clusters},${cluster_name_item}
        else
          k8s_clusters=${cluster_name_item}
        fi
      fi
    done
    if [ -n "${k8s_clusters}" ]; then
      export K8S_CLUSTER_NAMES=${k8s_clusters}
    fi
  fi

python /project/reserve_cluster.py
