#!/bin/bash -e
pushd $(dirname "$0")

IMAGE_VERSION=0.7
IMAGE_NAME=docker.wdf.sap.corp:51055/hanalite-vora:$IMAGE_VERSION
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME

popd
