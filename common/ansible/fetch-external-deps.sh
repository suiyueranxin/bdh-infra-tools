#!/usr/bin/env bash
# Install external roles
ROOTDIR="$(cd "$(dirname "${BASH_SOURCE-$0}")" && pwd)"
echo "Installing external roles"
mkdir -p ${ROOTDIR}/external-roles
ansible-galaxy install --ignore-certs williamyeh.oracle-java -p ${ROOTDIR}/external-roles
