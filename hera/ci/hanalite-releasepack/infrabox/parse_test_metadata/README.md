# test-metadata-parse
Read and analyze test-metadata from test image, and Post the result to dashboard.
## Build: 
- build context:  
    root of project bdh-infra-tools
- build command:  
docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/register_test_metadata:0.1 -f hera/ci/hanalite-releasepack/infrabox/parse_test_metadata/Dockerfile .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/register_test_metadata:0.1
## Current Version:
- master: di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/register_test_metadata:0.4

- rel-3.0 / rel-3.1 : no need

- rel-2013 : di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/register_test_metadata:0.1

- rel-2103 : di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/register_test_metadata:0.3

- rel-2104 : di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/register_test_metadata:0.3
## Required env when run container: 
  - CODELINE 
  - RELEASEPACK_VERSION 
  - DEPLOYTYPE 
  - USE_FOR 
