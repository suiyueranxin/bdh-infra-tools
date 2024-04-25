# Docker base repo
'**ansible-runtime-base**' is the based docker image and be used by other ansible runtime docker files.
If you changed this docker file, please push to the repo like below:
```
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible-runtime-base:latest
```

# Build images

To build the images, please use folder **bdh-infra-tools** as the root.

# Image Updates
```
docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:1.0 -f common/dockerfiles/alpine_ssh_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:1.0

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_and_push_images_with_kc:kc1.13.8_pyclient10.0.1 -f common/dockerfiles/build_and_push_images_with_kc .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_and_push_images_with_kc:kc1.13.8_pyclient10.0.1 

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible-runtime-base-ubuntu-18:0.1 -f common/dockerfiles/ansible-runtime-base-ubuntu-18 .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible-runtime-base-ubuntu-18:0.1

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_and_push_images_ubuntu:0.1 -f common/dockerfiles/build_and_push_images_ubuntu .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_and_push_images_ubuntu:0.1

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_and_push_images_ubuntu_gsutil:0.1 -f common/dockerfiles/build_and_push_images_ubuntu_gsutil .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_and_push_images_ubuntu_gsutil:0.1

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/bit-runtime:0.2 -f hera/ci/hanalite-releasepack/infrabox/build_and_run_images/Dockerfile .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/bit-runtime:0.2

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_vflow_test_with_kc:kc1.13.8_k8s10 -f alpine_vflow_test_with_kc .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_vflow_test_with_kc:kc1.13.8_k8s10

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/vflow_with_kc:kc1.13.8_k8s10 -f vflow_with_kc .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/vflow_with_kc:kc1.13.8_k8s10

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build-and-push-images-base:awscli_1_16_kc1.13.8 -f ./common/dockerfiles/build_and_push_images_with_kc_awscli .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build-and-push-images-base:awscli_1_16_kc1.13.8

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/import_export_test_base:with_docker_k8s10 -f import_export_test_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/import_export_test_base:with_docker_k8s10

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_python_with_dateutil:0.1 -f alpine_python_with_dateutil .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_python_with_dateutil:0.1

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_upgrade_test_vctl:0.2 -f alpine_upgrade_test_vctl .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_upgrade_test_vctl:0.2

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/vsystem_upgrade_base:0.3 -f vsystem_upgrade_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/vsystem_upgrade_base:0.3


docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_log_collection_base:0.4 -f ./common/dockerfiles/alpine_log_collection_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_log_collection_base:0.4 

docker build -f common/dockerfiles/get-full-product-stack -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/get-full-product-stack:0.5 .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/get-full-product-stack:0.5

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/trigger_milestone_validation_base:0.1 -f ./common/dockerfiles/trigger_milestone_validation_base .

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_check_test_metadata:1.2 -f ./common/dockerfiles/alpine_check_test_metadata .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_check_test_metadata:1.2

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-manager/ansible_runtime_on_ccloud:0.1 -f ./common/dockerfiles/ansible_runtime_on_ccloud .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-manager/ansible_runtime_on_ccloud:0.1

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/clone-bdh-infra-tools:0.1 -f ./common/dockerfiles/clone_bdh-infra-tools .

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/pylint_check_base:0.1 -f pylint_check_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/pylint_check_base:0.1

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/python3_slim_base:0.1 -f python3_slim_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/python3_slim_base:0.1

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/python3_slim_base_conn:0.1 -f python3_slim_base_conn .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/python3_slim_base_conn:0.1

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible-runtime-base:ansible4.0.0 -f ansible-runtime-base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible-runtime-base:ansible4.0.0

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_aks_base:ansible4.0.0 -f ansible_runtime_aks_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_aks_base:ansible4.0.0


docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_aks_base_conn:ansible4.0.0 -f ansible_runtime_aks_base_conn .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_aks_base_conn:ansible4.0.0

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_eks_base:ansible4.0.0 -f ansible_runtime_eks_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_eks_base:ansible4.0.0

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_eks_base_conn:ansible4.0.0 -f ansible_runtime_eks_base_conn .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_eks_base_conn:ansible4.0.0

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_gcloud_base:ansible4.0.0 -f ansible_runtime_gcloud_base .
docker push  di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_gcloud_base:ansible4.0.0

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_gcloud_base_conn:ansible4.0.0 -f ansible_runtime_gcloud_base_conn .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_gcloud_base_conn:ansible4.0.0

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-manager/ansible_runtime_on_ccloud_base:ansible4.0.0 -f ansible_runtime_on_ccloud_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-manager/ansible_runtime_on_ccloud_base:ansible4.0.0

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-manager/ansible_runtime_on_ccloud_base_conn:ansible4.0.0 -f ansible_runtime_on_ccloud_base_conn .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-manager/ansible_runtime_on_ccloud_base_conn:ansible4.0.0
```
# Image **NOT** Used
```
docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_and_push_images_with_kc_awscli_skopeo:awscli_1_16_skopeo_kc1.13.8 -f ./common/dockerfiles/build_and_push_images_with_kc_awscli_skopeo .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_and_push_images_with_kc_awscli_skopeo:awscli_1_16_skopeo_kc1.13.8

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_aks_base_with_latest_skopeo:0.0.01 -f ./common/dockerfiles/ansible_runtime_aks_base_with_latest_skopeo .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_aks_base_with_latest_skopeo:0.0.01

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_eks_base_with_latest_skopeo:0.0.01 -f ./common/dockerfiles/ansible_runtime_eks_base_with_latest_skopeo .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_eks_base_with_latest_skopeo:0.0.01

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible-runtime-gcloud-base-with-latest-skopeo:0.0.01 -f ./common/dockerfiles/ansible_runtime_gcloud_base_2 .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible-runtime-gcloud-base-with-latest-skopeo:0.0.01

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build-and-push-images-base-with-latest-skopeo:0.0.01 -f ./common/dockerfiles/build_and_push_image_base_with_latest_skopeo .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build-and-push-images-base-with-latest-skopeo:0.0.01

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build-and-push-images-base:awscli_1_16_skopeo_kc1.13.8 -f ./common/dockerfiles/build_and_push_images_with_kc_awscli_skopeo .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build-and-push-images-base:awscli_1_16_skopeo_kc1.13.8

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible-runtime-gcloud-base:k8s_1.13_helm_2.17_with_jq_and_skopeo_with_def_conn4_with_az_cli -f common/dockerfiles/ansible_runtime_gcloud_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible-runtime-gcloud-base:k8s_1.13_helm_2.17_with_jq_and_skopeo_with_def_conn4_with_az_cli

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible-runtime-gcloud-base_2:def_conn4 -f common/dockerfiles/ansible_runtime_gcloud_base_2 .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible-runtime-gcloud-base_2:def_conn4

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_eks_base:k8s_1.13_helm_2.17_with_skopeo_ssh_with_def_conn4_with_az_cli -f common/dockerfiles/ansible_runtime_eks_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_eks_base:k8s_1.13_helm_2.17_with_skopeo_ssh_with_def_conn4_with_az_cli

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_python_with_kc:kc1.13.8_k8s10_with_def_conn5 -f common/dockerfiles/alpine_python_with_kc .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_python_with_kc:kc1.13.8_k8s10_with_def_conn5

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_generator_with_kc:kc1.13.8 -f alpine_generator_with_kc .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_generator_with_kc:kc1.13.8

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/app_test_base:node12_k8s10 -f common/dockerfiles/app_test_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/app_test_base:node12_k8s10

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_aks_base:kc1.13.8_helm2.11_with_skopeo_with_def_conn4 -f common/dockerfiles/ansible_runtime_aks_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/ansible_runtime_aks_base:kc1.13.8_helm2.11_with_skopeo_with_def_conn4

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/hanawire_test_base:k8s_10 -f hanawire_test_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/hanawire_test_base:k8s_10

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_vsystem_test_with_docker_gke:go1.13.3_k8s10 -f alpine_vsystem_test_with_docker_gke .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_vsystem_test_with_docker_gke:go1.13.3_k8s10

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_check_test_metadata:1.0 -f ./common/dockerfiles/alpine_check_test_metadata .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_check_test_metadata:1.0

docker build -t di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/app_test_base:node14_k8s10 -f common/dockerfiles/app_test_base .
docker push di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/app_test_base:node14_k8s10

```
