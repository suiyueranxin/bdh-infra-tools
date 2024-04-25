#!/bin/bash

set -e # fail on error

pushd /vora

git config origin.url "ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-vora"
git config origin.fetch "+refs/heads/*:refs/remotes/origin/*"

export HAPPY_MAKE_CACHE=/infrabox/local-cache/hm-cache
export ELVIS_ARG_VERBOSE= # pass --verbose to activate extra verbosity

function checkout_vora()
{
  echo "## validating change in vora itself: $GERRIT_REFSPEC"
  git fetch origin $GERRIT_REFSPEC
  git checkout FETCH_HEAD
  git submodule update --init --recursive
}

function checkout_current_vora()
{
  echo "## update vora to current status"
  git fetch origin master
  git checkout FETCH_HEAD
  git submodule update --init --recursive
}

function checkout_current_codeline()
{
  echo "## checkout current codeline: $CODELINE"
  ./scripts/elvis.py \
    --codeline $CODELINE \
    --checkout-current \
    ${ELVIS_ARG_COMPONENTS} \
    ${ELVIS_ARG_VERBOSE}
}

function checkout_gerrit_component()
{
  echo "## validating change in gerrit component: ${GERRIT_REFSPEC}"
  ./scripts/elvis.py \
    --codeline $CODELINE \
    --checkout-change ${GERRIT_REFSPEC} \
    --gerrit-user InfraBox \
    ${ELVIS_ARG_COMPONENTS} \
    ${ELVIS_ARG_VERBOSE}
}

function checkout_github_component()
{
  echo "## validating branch in github component: ${CURRENT_COMPONENT}:${INFRABOX_GIT_BRANCH}"
  ./scripts/elvis.py \
    --codeline $CODELINE \
    --checkout-change ${CURRENT_COMPONENT}:${INFRABOX_GIT_BRANCH} \
    --gerrit-user InfraBox \
    ${ELVIS_ARG_COMPONENTS} \
    ${ELVIS_ARG_VERBOSE}
}

function checkout_pull_request()
{
  echo "## validating change in component, pull request: ${GITHUB_PULL_REQUEST_NUMBER}"
  ./scripts/elvis.py \
    --checkout-change ${CURRENT_COMPONENT}/pull/${GITHUB_PULL_REQUEST_NUMBER} \
    ${ELVIS_ARG_COMPONENTS} \
    ${ELVIS_ARG_VERBOSE}
}

if [ ! -z "${GERRIT_REFSPEC}" ]; then
  if [ ! -z "${GERRIT_PROJECT}" ] && [[ "${GERRIT_PROJECT}" == "hanalite-vora" ]];  then
    checkout_vora
  else
    checkout_current_vora
    checkout_current_codeline
    checkout_gerrit_component
  fi
elif [ ! -z "${GITHUB_PULL_REQUEST_NUMBER}" ]; then
  checkout_current_vora
  checkout_current_codeline
  checkout_pull_request
elif [ ! -z "${INFRABOX_GIT_BRANCH}" ]; then
  checkout_current_vora
  checkout_current_codeline
  checkout_github_component
else
  checkout_current_vora
  checkout_current_codeline
  echo "### [level=warning] not validating a specific change or pull request"
fi

popd
