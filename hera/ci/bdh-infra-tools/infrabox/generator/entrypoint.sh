#!/bin/bash
set -x
# get current bdh-infra-tools commit id

source /project/get_latest_commit_id.sh

is_test_cycle_config_change_only() {
  TEST_CYCLE_CONF_FOLDER_NAME=${TEST_CYCLE_CONF_FOLDER_NAME:-"TestCycleConfiguration"}
  # check if the commit only contains the changes in TestCycleConfiguration folder
  git diff --name-only HEAD^..HEAD | awk -F '/' '{print $1}' | uniq | grep -v ${TEST_CYCLE_CONF_FOLDER_NAME}
  if [[ $? -ne 0 ]]; then
    echo "## files changes only in ${TEST_CYCLE_CONF_FOLDER_NAME}. Skip the validation job."
    return 0
  fi
  return 1
}

is_skip_validation() {
  python /project/check_skip_validation.py /project/git_log
  if [[ $? -eq 0 ]]; then
    echo "## skip validation is found in git log."
    return 0
  fi
  return 1
}

if [[ $GERRIT_CHANGE_PROJECT ]] && [[ "$GERRIT_CHANGE_PROJECT" == "hanalite-releasepack" ]]; then
  get_latest_commit_id $GERRIT_PATCHSET_REF
else
  get_latest_commit_id
fi
if [[ -n "${GERRIT_CHANGE_COMMIT_MESSAGE}" ]]; then
  echo "${GERRIT_CHANGE_COMMIT_MESSAGE}" >> /project/git_log
  sed -i 's/\\n/\n/g' /project/git_log
else
  # goto the code folder and use git log to get logs
  pushd /infrabox/context
    git --no-pager log -1 --pretty=%B >> /project/git_log
  popd
fi

pushd /project
  source /project/common.sh
  echo "## starting clone hanalite releasepack"
  clone_hanalite_releasepack
  LATEST_MILESTONE_VERSION=$(cat hanalite-releasepack/cfg/VERSION)
  export BUILD_VERSION="${LATEST_MILESTONE_VERSION}-${INFRABOX_BUILD_NUMBER}"
  echo BUILD_VERSION
  # for push validation, exit job if the changes only within test cycle folder.
  if [[ $GERRIT_CHANGE_PROJECT ]] && [[ "$GERRIT_CHANGE_PROJECT" == "hanalite-releasepack" ]] && [[ ${GERRIT_PATCHSET_REF} ]] && [[ -n ${GERRIT_PATCHSET_REF} ]]; then
    pushd /project/hanalite-releasepack
      if is_test_cycle_config_change_only && is_skip_validation; then
        exit 0
      fi
    popd
  fi
echo "## clone hanalite releasepack finshed"
popd

echo "## generate push_val infrabox.json with test jobs"
infraboxjson=$(cat /project/hanalite-releasepack/TestCycleConfiguration/push_val_infrabox.json)




#infraboxjson=$(cat /project/push_val_infrabox.json)
infraboxjson=${infraboxjson//DUMMY_REPLACE_VERSION/$BUILD_VERSION}
infraboxjson=${infraboxjson//DUMMY_REPLACE_BRANCH/$GERRIT_CHANGE_BRANCH}
echo $infraboxjson > /project/infrabox_tmp.json

python /project/entrypoint.py /project/git_log /project/infrabox_tmp.json

if [ ! -f "/project/infrabox_adapt.json" ]; then
  echo "## failed to adapt infrabox.json"
  exit 1
fi

cp /project/infrabox_adapt.json /infrabox/output/infrabox.json
cp /infrabox/output/infrabox.json /infrabox/upload/archive/

