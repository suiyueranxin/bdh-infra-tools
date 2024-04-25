#!/bin/bash
set -x

if [ "$INFRABOX_GITHUB_PULL_REQUEST" != "true" ]; then
  echo "## This is not a push validation, exit!"
  exit 0
fi

if [ -z "$GITHUB_PULL_REQUEST_BASE_REF" ]; then
  echo "## No GITHUB_PULL_REQUEST_BASE_REF, exit!"
  exit 0
fi

pushd /infrabox/context/
ls -al
git status
git config --global http.sslVerify false
git config remote.origin.url ${GITHUB_PULL_REQUEST_BASE_REPO_CLONE_URL}
git config remote.origin.fetch +refs/heads/*:refs/remotes/origin/*
git fetch origin ${GITHUB_PULL_REQUEST_BASE_REF}

PY_CHANGES=$(git --no-pager diff --name-only --diff-filter=ACM FETCH_HEAD | grep "\.py\{0,1\}$" | wc -l)

if [ ! ${PY_CHANGES} -eq 0 ];then
  git --no-pager diff --name-only --diff-filter=ACM FETCH_HEAD | grep "\.py\{0,1\}$"  > pylint_check/pythonchangelist

  echo "this PR python file change list as following:"
  cat pylint_check/pythonchangelist
  chmod +x pylint_check/pylint_git.sh
  pylint_check/pylint_git.sh pylint_check/pythonchangelist

  if [[ "$?" != 0 ]]; then
    echo "Pylint Failed"
    exit 1
  fi
  echo "## Pylint Check done..."

else
  echo "this PR no pthon file change"
  exit 0
fi

popd
