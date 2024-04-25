FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:1.0 AS ssh_base

FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_python_with_kc:kc1.13.8_k8s10
COPY hera/common/common.sh /project/common.sh

COPY hera/ci/hanalite-releasepack/infrabox/feature_toggle/* /project/
COPY --from=ssh_base /root/.ssh/* /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa-gerrit

WORKDIR /project
ENTRYPOINT [ "bash", "entrypoint.sh" ]
