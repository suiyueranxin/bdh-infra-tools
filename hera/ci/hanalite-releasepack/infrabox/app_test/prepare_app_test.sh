#!/bin/bash
set -ex

echo "## apps test start..."
source /project/common.sh
# port-forward to solve the ingress url access cloud issue from vctl
vsystem_pod=$(kubectl -n $NAMESPACE get po -l vora-component=vsystem -o jsonpath='{.items[0].metadata.name}')
vsystem_svc=vsystem-ext
PID=
if ! port_forward ${vsystem_svc} 8797 service; then
  cat << EOF >> /infrabox/upload/archive/error_msg.log
health_check: Connection to Data Hub Error(PORT FORWARD)
EOF
  die "## pord-forward failed!"
fi
export PORT_FORWARD_PID=${PID}
sleep 1
export VSYSTEM_URL=https://127.0.0.1:8797
export VSYSTEM_HOST=$VSYSTEM_ENDPOINT
if [[ $CLOUD_ONLY ]] && [[ "$CLOUD_ONLY" == "1" ]]; then
  cloud_param='--cloud'
  if [[ $PROVISION_PLATFORM ]] && [[ "$PROVISION_PLATFORM" == "GKE" ]]; then
    cloud_param='--cloud --platform GCP'
  fi
  if [[ $PROVISION_PLATFORM ]] && [[ "$PROVISION_PLATFORM" == "AWS-EKS" ]]; then
    cloud_param='--cloud --platform AWS'
  fi
  if [[ $PROVISION_PLATFORM ]] && [[ "$PROVISION_PLATFORM" == "DHAAS-AWS" ]]; then
    cloud_param='--platform AWS --dhaas'
  fi
  if [[ $PROVISION_PLATFORM ]] && [[ "$PROVISION_PLATFORM" == "AZURE-AKS" ]]; then
    cloud_param='--cloud --platform AZU'
  fi
else
  cloud_param=''
fi

#echo "Get HANA password"
#hana_pwd=$(kubectl -n $NAMESPACE get secrets vora.conf.hana-password -o 'go-template={{index .data "password.json"}}' | base64 -d | cut -d ':' -f 2 | tr -d '}"')
#echo "## hana password is $hana_pwd"
#
#echo "Set options datahub.app.db.credentials by vctl "
#vctl --insecure login $VSYSTEM_URL $VORA_TENANT $VORA_USERNAME $VORA_PASSWORD
#vctl apps param set datahub.app.db.credentials "{\"host\":\"hana-service.$NAMESPACE\",\"port\":\"30017\",\"user\":\"SYSTEM\",\"password\":\"$hana_pwd\",\"schema\":\"DATAHUB\",\"hdi_user\":\"SYSTEM\",\"hdi_password\":\"$hana_pwd\"}"
#vctl apps param get datahub.app.db.credentials
get_e2e_branch() {
  if [[ -n ${GERRIT_CHANGE_BRANCH} ]]; then
    if [[ ${GERRIT_CHANGE_BRANCH} =~ ^rel ]]; then
      if [[ "${GERRIT_CHANGE_BRANCH}" == "rel-3.0" ]]; then
        E2E_GIT_BRANCH="rel-3.0.2"
      else
        branch_prefix=$(echo $GERRIT_CHANGE_BRANCH | cut -d '-' -f2 | cut -d '.' -f1)
        git config --global http.sslVerify false
        branch_exists=$(git ls-remote --heads git@github.wdf.sap.corp:bdh/datahub-e2e-test.git $GERRIT_CHANGE_BRANCH | wc -l)
        if [ $branch_exists -eq 0 ]; then
          echo "E2E test branch ${GERRIT_CHANGE_BRANCH} not exist, use master by default"
          E2E_GIT_BRANCH="master"
        else
          E2E_GIT_BRANCH=${GERRIT_CHANGE_BRANCH}
        fi
      fi
    else
      E2E_GIT_BRANCH=${GERRIT_CHANGE_BRANCH}
    fi
  else
    get_e2e_branch_by_ver ${VORA_VERSION}
  fi
}

E2E_GIT_BRANCH="master"
if [[ -z ${UPGRADE_TEST} ]]; then
  get_e2e_branch
else
  if [[ ${UPGRADE_TEST} == "PREPARATION" || ${UPGRADE_TEST} == "VALIDATION" || ${UPGRADE_TEST} == "TEARDOWN" ]]; then
    if [[ -n ${BASE_BDH_VERSION} ]]; then
      get_e2e_branch_by_ver ${BASE_BDH_VERSION}
    else
      get_e2e_branch
    fi
  fi
fi

if [[ "${USE_FOR}" == "AUTO_ENV" ]]; then
  if [[ -z ${UPGRADE_TEST} ]]; then
    get_e2e_branch
  else
    if [[ -n ${BASE_BDH_VERSION} ]]; then
      get_e2e_branch_by_ver ${BASE_BDH_VERSION}
    else
      get_e2e_branch
    fi
  fi
fi


# run test
git config --global http.sslVerify "false"
git clone git@github.wdf.sap.corp:bdh/datahub-e2e-test.git
pushd datahub-e2e-test

if [[ ${E2E_GIT_BRANCH} ]] && [[ -n ${E2E_GIT_BRANCH} ]]; then
  git checkout ${E2E_GIT_BRANCH}
else
  echo "## Get E2E_GIT_BRANCH Failed!"
fi

npm cache clean --force
npm install

echo "### [level=info] The smoke test is ready to be performed."
echo "Port forward process id: ${PORT_FORWARD_PID}"
