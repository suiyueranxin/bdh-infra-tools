#!/bin/bash
set -x
source /project/common.sh
echo "## Start to copy files from build job..."

input_dir=$(dirname $(find /infrabox/inputs -mindepth 2 -maxdepth 2 -name env.sh))
if ! [ -d "$input_dir" ]; then
  echo "Cannot find env.sh in any folder in /infrabox/inputs, checkout the hanalite-releasepack/pom.xml"
  pushd /project
    clone_hanalite_releasepack
  popd
  pushd /project/hanalite-releasepack
    get_component_version_from_pom
  popd
else
  cp -v ${input_dir}/env.sh /infrabox/output/env.sh
  cp -v ${input_dir}/recent_commit_log /infrabox/output/recent_commit_log
  cp -v ${input_dir}/recent_commit_log.json /infrabox/output/recent_commit_log.json
  cp -v ${input_dir}/vorabuild.log /infrabox/output/vorabuild.log
  
  if [ -f ${input_dir}/installation_config.sh ]; then
    cp -v ${input_dir}/installation_config.sh /infrabox/output/installation_config.sh
  fi
fi

echo "Copy files done..."
