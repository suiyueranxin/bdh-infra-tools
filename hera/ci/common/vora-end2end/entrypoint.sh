#!/bin/bash

set -ex

#support git clone for https 
git config --global url."${GITHUB_BASE_URL}".insteadOf "https://github.wdf.sap.corp"
git config --global http.sslVerify false

/e2e/checkout.sh
source /e2e/common.sh

pushd /vora #infrabox/context

git config origin.url "ssh://InfraBox@git.wdf.sap.corp:29418/hanalite-vora"
git config origin.fetch "+refs/heads/*:refs/remotes/origin/*"

export HAPPY_MAKE_CACHE=/infrabox/local-cache/hm-cache
export CCACHE_DIR=/infrabox/local-cache/ccache
export ELVIS_ARG_VERBOSE=  # pass --verbose for extra verbosity
mkdir -p $CCACHE_DIR
ccache -M 100G
ccache -F 0

if [ -z "${GERRIT_REFSPEC}" ] && [ -d /infrabox/context ] && [ -n "${CURRENT_COMPONENT}" ]; then
  echo "## override ${CURRENT_COMPONENT} content with infrabox context"
  rsync \
    --recursive \
    --links \
    --dirs \
    --quiet \
    --delete \
    --exclude=.git \
    --exclude=.infrabox \
    --exclude=build \
    /infrabox/context ${CURRENT_COMPONENT}
fi

echo "## cache stats"
ccache -s

echo "## elvis build"
./scripts/elvis.py \
  ${ELVIS_ARG_COMPONENTS} \
  --build \
  --xmake-clean-after-build \
  ${ELVIS_ARG_VERBOSE}

echo "## cache stats"
ccache -s

echo "## archiving"
if [ -f test_suites.xml ]; then
  mv -v test_suites.xml /infrabox/upload/testresult
fi

if [ -d /vora/build/logs ]; then
  cp -v /vora/build/logs/vora.log /infrabox/output/vorabuild.log
  mkdir -p /infrabox/upload/archive/
  mv -v /vora/build/logs /infrabox/upload/archive/
fi

function move2output() {
  pattern=$1
  target_file_name=$2

  package=$(find /vora/build/mvn_repo/ -name "$pattern" | head -n 1)
  if ! [ -f "$package" ]; then
    echo "Could not find '$pattern'"
    return 1
  fi
  mv -v "$package" "/infrabox/output/$target_file_name"
}

move2output \*Foundation.tar.gz Foundation.tar.gz
move2output \*DI-Assembly.tar.gz DI-Assembly.tar.gz

component=hanalite-releasepack
VORA_VERSION=$($(git rev-parse --show-toplevel)/scripts/elvis.py -c "$component" --show-version |& grep ":$component: current" | sed "s/^.*:$component: current \(.*\)/\1/")
if [ -z "${VORA_VERSION}" ]; then
  echo "Version was not fetched correctly"
  exit 1
fi
echo "export VORA_VERSION=$VORA_VERSION" >> /infrabox/output/env.sh
echo "export CURRENT_COMPONENT=$CURRENT_COMPONENT" >> /infrabox/output/env.sh

git -C components/${CURRENT_COMPONENT} log -10 --date-order > /infrabox/output/recent_commit_log
git -C components/${CURRENT_COMPONENT} log -10 --date-order --pretty=format:'{%n  "commit": "%H",%n  "author": "%aN <%aE>",%n  "date": "%ad",%n  "message": "%f"%n},' $@ | perl -pe 'BEGIN{print "["}; END{print "]\n"}' | perl -pe 's/},]/}]/' > /infrabox/output/recent_commit_log.json

pushd components/${component}
  cp /e2e/*.py ./
  get_component_version_from_pom
popd

echo "## /infrabox/output/env.sh"
cat /infrabox/output/env.sh

echo "## /infrabox/output/recent_commit_log"
cat /infrabox/output/recent_commit_log

echo "## /infrabox/output/recent_commit_log.json"
cat /infrabox/output/recent_commit_log.json

popd
