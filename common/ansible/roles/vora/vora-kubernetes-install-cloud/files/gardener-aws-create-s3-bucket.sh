#!/bin/bash

if [ x$2 == "xus-east-1" ];then
  aws s3api create-bucket --bucket $1 --region $2
else
  aws s3api create-bucket --bucket $1 --region $2 --create-bucket-configuration LocationConstraint=$2
fi
aws s3api put-bucket-versioning --bucket $1 --versioning-configuration Status=Enabled
