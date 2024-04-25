#!/bin/bash
set -x

function get_latest_commit_id()
{
  # input option: GERRIT_PATCHSET_REF (optional)
  # output:
  #   COMMIT_ID_MASTER and COMMIT_ID_STABLE when no input option
  #   COMMIT_ID when GERRIT_PATCHSET_REF is set
  # Note: if CODELINE is set, it always chckout CODELINE branch and set the COMMID_ID with the latest
  if [ $# -ne 0 ]; then
    PATCHSET=$1
  fi
  BRANCH_ARR="master stable"

  TMP_FOLDER=$(mktemp -d /tmp/foo.XXXXXXXXX)
  RELEASEPACK_REPO="ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-releasepack"
  GET_COMMID="git ls-files -s bdh-infra-tools | cut -d ' ' -f2"

  if [ -z ${TMP_FOLDER} ]; then
    echo "tmp folder create failed! exit!"
    return
  fi

  pushd ${TMP_FOLDER}
  git clone ${RELEASEPACK_REPO}
  pushd hanalite-releasepack
    if [[ -n ${CODELINE} ]]; then
      echo "CODELINE=${CODELINE} then ignore GERRIT_PATCHSET_REF"
      git checkout ${CODELINE}
      export COMMIT_ID=$(eval $GET_COMMID)
    elif [[ -n "$PATCHSET" ]]; then
      git fetch ${RELEASEPACK_REPO} ${PATCHSET} && git checkout FETCH_HEAD
      export COMMIT_ID=$(eval $GET_COMMID)
    else
      for BRANCH in $BRANCH_ARR;
      do
        git checkout $BRANCH
        if [[ $BRANCH == "master" ]]; then
          export COMMIT_ID_MASTER=$(eval $GET_COMMID)
        fi
        if [[ $BRANCH == "stable" ]]; then
          export COMMIT_ID_STABLE=$(eval $GET_COMMID)
        fi
      done
    fi
  popd
  rm -rf hanalite-releasepack
  popd
  rm -rf ${TMP_FOLDER}
}
