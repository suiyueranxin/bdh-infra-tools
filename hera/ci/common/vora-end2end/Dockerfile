FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:1.0 AS ssh_base
FROM docker.wdf.sap.corp:51055/hanalite-vora:0.7

ARG CODELINE
ENV CODELINE=${CODELINE}
ARG GITHUB_BASE_URL
ENV GITHUB_BASE_URL=$GITHUB_BASE_URL
ADD hera/ci/common/vora-end2end/entrypoint.sh /e2e/entrypoint.sh
ADD hera/ci/common/vora-end2end/checkout.sh /e2e/checkout.sh
COPY hera/common/common.sh common/ansible/tools/get_component_version.py common/ansible/tools/list_component_versions.py /e2e/
RUN chmod +x /e2e/*.py && chmod +x /e2e/*.sh
COPY --from=ssh_base /root/.ssh/* /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa-gerrit
CMD /e2e/entrypoint.sh
