#!/bin/bash

folder_name=$1
bucket=$2
set -e

echo "Removing all versions from $bucket/$folder_name"

versions=`aws s3api list-object-versions --bucket $bucket --prefix $folder_name |jq '.Versions'`
markers=`aws s3api list-object-versions --bucket $bucket --prefix $folder_name  |jq '.DeleteMarkers'`
count_temp=$(echo $versions |jq 'length')
if [[ $count_temp -ne 1 ]]; then
    let count=count_temp-1
else
    count=0
fi

if [ $count -gt -1 ]; then
        echo "removing files"
        for i in $(seq 0 $count); do
                key=`echo $versions | jq .[$i].Key |sed -e 's/\"//g'`
                versionId=`echo $versions | jq .[$i].VersionId |sed -e 's/\"//g'`
                cmd="aws s3api delete-object --bucket $bucket --key $key --version-id $versionId"
                #echo $cmd
                $cmd
        done
fi

count_temp=$(echo $markers |jq 'length')
if [[ $count_temp -ne 1 ]]; then
    let count=count_temp-1
else
    count=0
fi

if [ $count -gt -1 ]; then
        echo "removing delete markers"

        for i in $(seq 0 $count); do
                key=`echo $markers | jq .[$i].Key |sed -e 's/\"//g'`
                versionId=`echo $markers | jq .[$i].VersionId |sed -e 's/\"//g'`
                cmd="aws s3api delete-object --bucket $bucket --key $key --version-id $versionId"
                #echo $cmd
                $cmd
        done
fi

echo "Removing bucket folder $bucket/$folder_name"
