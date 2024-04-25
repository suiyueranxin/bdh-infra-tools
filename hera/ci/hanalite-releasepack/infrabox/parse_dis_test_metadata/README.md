# dis_test-metadata-parse
Read and analyze dis_test-metadata from test image, and Post the result to dashboard.
## Build: 
- build context:  
    root of project bdh-infra-tools
- build command:  
docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/register_dis_test_metadata:0.1 -f hera/ci/hanalite-releasepack/infrabox/parse_dis_test_metadata/Dockerfile .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/register_dis_test_metadata:0.1
## Required env when run container: 
  - CODELINE
  - USE_FOR 
