#!/bin/bash

python registry.py -r https://di-dev-cicd-docker.int.repositories.cloud.sap --delete-all --no-validate-ssl --images-like "bdh-infra-tools/troubleshooting/*"
