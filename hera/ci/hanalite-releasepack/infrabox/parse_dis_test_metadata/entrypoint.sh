set -x

# Get the components version from env.sh
if [ -n "${PARENT_INSTALL_JOB}" ]; then
  ENV_FILE="/infrabox/inputs/${PARENT_INSTALL_JOB}/env.sh"
  if [ ! -f ${ENV_FILE} ]; then
    echo "${ENV_FILE} does not exist."
    exit 1
  else
    source ${ENV_FILE}
  fi
else
  echo "### [level=warning] Skip sourcing env.sh, Using external env information..."
fi

source /project/common.sh

if [ -z "$GERRIT_CHANGE_BRANCH" ]; then
    export GERRIT_CHANGE_BRANCH="master"
fi
if [ -z "$INFRABOX_GIT_BRANCH" ]; then
    export INFRABOX_GIT_BRANCH="master"
fi

if [[ $INFRABOX_GIT_BRANCH == pr-test-val-* ]]; then
    echo "## Skip parse metadata for branch pr-test-val-*"
    exit 0
fi

pushd /project
    if [ -d "/project/dis-release/" ]; then
    rm -rf /project/dis-release
    fi
    clone_repo "git@github.wdf.sap.corp:bdh/dis-release.git" ${INFRABOX_GIT_BRANCH}
    ccm_jobs_file=/project/dis-release/milestone-validation/smoke_tests_jobs_CCM.json
    dwc_jobs_file=/project/dis-release/milestone-validation/smoke_tests_jobs_DWC.json
    hc_jobs_file=/project/dis-release/milestone-validation/smoke_tests_jobs_HC.json
    pushd /project/dis-release
        if ! [ -f "${ccm_jobs_file}" ] || ! [ -f "${dwc_jobs_file}" ] || ! [ -f "${hc_jobs_file}" ]; then
            echo "get jobs failed"
            exit 1
        fi
        cp ${ccm_jobs_file} /project/smoke_tests_jobs_CCM.json
        cp ${dwc_jobs_file} /project/smoke_tests_jobs_DWC.json
        cp ${hc_jobs_file} /project/smoke_tests_jobs_HC.json
    popd
popd

python3 /project/entrypoint.py
