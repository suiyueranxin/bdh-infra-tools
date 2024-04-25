# Introduction
This is image is used for get/set feature-toggle of DI. 
## Build: 
- build context:  
    root of project bdh-infra-tools
- build command:  
docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/handle_feature_toggle:0.1 -f hera/ci/hanalite-releasepack/infrabox/feature_toggle/Dockerfile .
di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/handle_feature_toggle:0.1
## Requiremend: 
  - DI was successufully installed
  - env.sh was an output of install job
