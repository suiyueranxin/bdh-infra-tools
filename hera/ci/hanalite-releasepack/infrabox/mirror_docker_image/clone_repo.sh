#!/bin/bash
set -ex

if [[ "${GERRIT_CHANGE_BRANCH}" =~ ^rel-2 ]] || [[ "${GERRIT_CHANGE_BRANCH}" == "master" ]]; then
    echo "## copy /infrabox/context to /infrabox/output/context"
    # we need to exclude .infrabox because this contains /infrabox/output
    rm -rf /infrabox/output/context
    mkdir /infrabox/output/context
    cd /infrabox/context
    tar cf - --exclude=.infrabox  . | tar xf - -C /infrabox/output/context/
else
    echo "master and rel-3.x push val use build job to clone"
fi
