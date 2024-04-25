#!/bin/bash
set -ex

mirror_image() {
  # $1 image list file name
  # $2 Create repo for DHAAS registry if it is not existed : "enable" or "forbidden"
  # $3 on "ignore mirror failure". "yes" or "no"
  ignore_failure="no" #default
  if [[ -n "$3" ]]; then
    echo "Ignore failure = $3"
    ignore_failure=$3
  fi

  # add pipe file FIFO and backgrand running for skopeo parallel
  tempfifo=$$.fifo

  # trap catch Interrupt command
  # if catch '1 SIGHUP Clean tidyup', '2 SIGINT Interrupt', '3 SIGQUIT Quit', '6 SIGABRT Abort', 
  # close the Write && Read on file descriptor 1000
  trap "exec 1000>&-;exec 1000<&-;exit 0" 1 2 3 6
  
  # Create a pipe file FIFO
  mkfifo $tempfifo

  # bound file descriptor 1000 and FIFO, '<' means Read bound, '>' means Write bound.
  # '<>' means all oprations on file descriptor 1000 equal to that on pipe file $tempfifo
  # The important feature of FIFO is that, the Read and write must exist simultaneously.
  # If one operation is missing, the other one will hang.
  exec 1000<>$tempfifo
  rm -rf $tempfifo

  # skopeo parallel numbers 
  if [[ -n "${SKOPEO_PARALLEL_NUMBERS}" ]]; then
      skopeo_parallel_numbers=${SKOPEO_PARALLEL_NUMBERS}
  else
      skopeo_parallel_numbers=5
  fi

  # Write on file descriptor 1000, insert '$skopeo_parallel_numbers' empty rows into file descriptor 1000
  # Write and Read on a pipe file based on the row as a unit
  for ((i = 1; i <= $skopeo_parallel_numbers; i++));
  do
    echo >&1000
  done

  for line in $(cat $1)
  do
    
    # read one empty row from file descriptor 1000, the row numbers minus 1
    read -u1000
    {
    pull_url=`echo $line | cut -d \; -f 1`
    push_url=`echo $line | cut -d \; -f 2`
    echo $pull_url
    echo $push_url

    pull_image_digest=$(skopeo inspect --raw --tls-verify=false docker://${pull_url} | jq '.config.digest')
    push_image_digest=$(skopeo inspect --raw --tls-verify=false docker://${push_url} | jq '.config.digest')

    if [ -z ${pull_image_digest} ]; then
      if [ -n ${push_image_digest} ]; then
        # image only exist on target registry
        echo "WARN: images [${pull_url}] not exist, but image [${push_url}] exist"
        # Write a new empty row into file descriptor 1000, when exit the for loop.
        echo >&1000
        continue
      fi
      # image not exist on both source and target registry
      echo "##  images [${push_url}] not exist"
      # Write a new empty row into file descriptor 1000, when exit the 'for line in $(cat $1)' loop.
      echo >&1000
      exit 1
    fi
    if [[ "${pull_image_digest}" == "${push_image_digest}" ]]; then
      echo "Skip image mirroring for ${push_url} (image already available)"
      # Write a new empty row into file descriptor 1000, when exit the 'for line in $(cat $1)' loop.
      echo >&1000
      continue
    else
      RETRY=5
      for ((i = 1; i <= ${RETRY}; i++)); do
        echo "## Create repo is ${2}"
        if [[ "${2}" == "enable" ]]; then
          #Get repo name from push_url
          repo_part=${push_url%%:*}
          repo_name=${repo_part#*/}
          #Check if repository exists
          set +e
          aws ecr describe-repositories --repository-names ${repo_name}
          check_repo_result=$?
          set -e
          if [ ${check_repo_result} -eq 0 ]; then
            echo "##  The repo [${repo_name}] was already existed"          
          else
            set +e
            aws ecr create-repository --repository-name ${repo_name}
            create_repo_result=$?
            set -e
            if [ ${create_repo_result} -eq 0 ]; then
              echo "##  Create repo [${repo_name}]"
            else
              echo "## Create repo failed"
            fi
          fi
        fi
        set +e
        skopeo copy docker://${pull_url} docker://${push_url}
        ret_code=$?
        set -e
        if [ ${ret_code} -ne 0 ]; then
          if [[ $i == ${RETRY} ]]; then
            if [[ ${ignore_failure} == "yes" ]]; then
              # skip and mirror next image
              break
            else
              echo "##  images [${push_url}] push fail!"
              # Write a new empty row into file descriptor 1000, when exit the 'for line in $(cat $1)' loop.
              echo >&1000
              exit 1
            fi
          fi
          echo "##  images [${push_url}] push fail! retry..."
          # retry what ever the $ignore_failure value
          continue
        else
          # skopeo copy succeed
          break
        fi
      done
      # Write a new empty row into file descriptor 1000, when exit the 'for line in $(cat $1)' loop.
      echo >&1000
    fi
    
    # All the operation in {} execute in the background 
    } &
  done

  # wait for the completion of all parallel skopeo processes.
  wait

  # close the Write && Read on file descriptor 1000
  exec 1000>&-
  exec 1000<&-

  echo "  skeopo mirror in parallel done!"
}

mirror_image_on_prem() {
  if [ ! -f /credential.json ]; then
    echo "## Get Credential From IM"
    AUTH_HEADER=$(cat /infrabox/inputs/${K8S_CREATION_JOB}/auth_header.txt)
    python ${ROOT_DIR}/tools/get_cloud_credentials.py ${K8S_CLUSTER_NAME} ${PROVISION_PLATFORM} "/" "${AUTH_HEADER}"
  fi

  if [[ ${PROVISION_PLATFORM} == "GKE" ]]; then
    gcloud auth activate-service-account --key-file=/credential.json
    gcloud config set project sap-p-and-i-big-data-vora
    gcloud docker -a
  elif [[ ${PROVISION_PLATFORM} == "AZURE-AKS" ]]; then
    # skopoe does not support Azure CR now: https://github.com/containers/skopeo/issues/533
    AZURE_CLIENT_ID=$(jq -r ".AZURE_CLIENT_ID" "/credential.json")
    AZURE_SUBSCRIPTION_ID=$(jq -r ".AZURE_SUBSCRIPTION_ID" "/credential.json")
    AZURE_TENANT=$(jq -r ".AZURE_TENANT" "/credential.json")
    AZURE_CLIENT_SECRET=$(jq -r ".AZURE_CLIENT_SECRET" "/credential.json")
    az login --service-principal --username $AZURE_CLIENT_ID --password $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT
    if [[ -n "${AKS_SUBSCRIPTION_NAME}" ]]; then
      az account set --subscription "${AKS_SUBSCRIPTION_NAME}"
    else
      az account set --subscription 'PI Big Data Vora (SE)'
    fi
    if [[ -n "${AZURE_REGISTRY_NAME}" ]]; then
      az acr login -n "${AZURE_REGISTRY_NAME}"
    else
      az acr login -n 'infrabase'
    fi
  elif [[ ${PROVISION_PLATFORM} == "AWS-EKS" ]] || [[ ${PROVISION_PLATFORM} == "GARDENER-AWS" ]]; then
    set +x
    AWS_ACCESS_KEY_ID=$(jq -r ".AWS_ACCESS_KEY" "/credential.json")
    AWS_SECRET_ACCESS_KEY=$(jq -r ".AWS_SECRET_KEY" "/credential.json")
    aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
    aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
    aws configure set region "eu-west-1"
    eval $(aws ecr get-login --no-include-email | sed 's|https://||')
    set +e
    if [[ -z ${EKS_DOCKER_REGISTRY_SUFFIX} ]]; then
      eval "$(cat /tmp/image_list | cut -d ':' -f1 | cut -d'/' -f2-3 | awk '{print "aws ecr create-repository --repository-name="$1}')"
    else
      eval "$(cat /tmp/image_list | cut -d ':' -f1 | cut -d'/' -f2-3 | awk '{print "aws ecr create-repository --repository-name=${EKS_DOCKER_REGISTRY_SUFFIX}/"$1}')"
    fi
    if [[ -n ${EKS_VFLOW_DOCKER_REGISTRY_SUFFIX} ]]; then
      eval "$(cat /tmp/image_list | cut -d ':' -f1 | cut -d'/' -f2-3 | awk '{print "aws ecr create-repository --repository-name=${EKS_VFLOW_DOCKER_REGISTRY_SUFFIX}/"$1}')"
    fi
    set -e
    set -x
  else
    echo "Privisioning type ${PROVISION_PLATFORM} not supported !"
    exit 1
  fi

  mirror_image "/tmp/pull_push_list" "forbidden" "yes"
}

mirror_image_on_cloud() {
  openssl s_client -connect public.int.repositories.cloud.sap -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM | tee /usr/local/share/ca-certificates/docker.wdf.sap.corp.crt
  openssl s_client -connect di-dev-cicd-docker.int.repositories.cloud.sap:443 -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM | tee /usr/local/share/ca-certificates/di-dev-cicd-docker.int.repositories.cloud.sap.crt
  openssl s_client -connect di-dev-cicd-v2.int.repositories.cloud.sap:443 -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM | tee /usr/local/share/ca-certificates/di-dev-cicd-v2.int.repositories.cloud.sap.crt
  update-ca-certificates

  set +x
  AWS_REGION="eu-central-1"
  aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
  aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
  aws configure set region $AWS_REGION
  eval $(aws ecr get-login --no-include-email | sed 's|https://||')
  set -x

  mirror_image "/project/pull_push_list" "enable" 
}

if [[ "${1}" == "on_cloud" ]]; then
  mirror_image_on_cloud
elif [[ "${1}" == "on_prem" ]]; then
  mirror_image_on_prem
fi

