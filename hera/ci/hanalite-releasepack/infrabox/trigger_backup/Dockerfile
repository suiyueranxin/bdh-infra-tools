FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_python_with_kc:kc1.13.8_k8s10

RUN mkdir -p /project
COPY hera/ci/hanalite-releasepack/infrabox/trigger_backup/entrypoint.sh /project/entrypoint.sh

ENTRYPOINT /project/entrypoint.sh