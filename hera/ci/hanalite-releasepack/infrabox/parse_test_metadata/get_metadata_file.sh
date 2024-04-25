#!/usr/bin/env bash
#inputs: {1}: component image
#        {2}: component tag
#        {3}: job name
#        {4}: metadata_file_path (optional)  
set +e  
set -x
mkdir -p /tmp/${3}
pushd /tmp/${3}
    python3 /project/docker_pull.py "${1}:${2}"
    metadata_file_path="metadata-config"

    if [ -d /project/metadata/${3} ]; then
        rm  -rf /project/metadata/${3}/*
    fi
    if [ -n "${4}" ];then
        metadata_file_path=${4}
    fi
    tar -xf *.tar && rm -f *.tar
    find . -name layer.tar -exec tar -xf {} \;
    if [ -f ${metadata_file_path} ]; then
        cp  ${metadata_file_path} /project/metadata/${3}/
    fi
    if [ -d ${metadata_file_path} ]; then
        cp -r ${metadata_file_path}/* /project/metadata/${3}/
    fi
    rm -rf /tmp/${3}/*
popd