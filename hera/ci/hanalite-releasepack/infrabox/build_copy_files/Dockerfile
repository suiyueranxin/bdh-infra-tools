FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:1.0 AS ssh_base
FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_base

RUN mkdir -p /project
COPY hera/ci/hanalite-releasepack/infrabox/build_copy_files/entrypoint.sh /project/entrypoint.sh
COPY common/ansible/tools/get_component_version.py /project/get_component_version.py
COPY common/ansible/tools/list_component_versions.py /project/list_component_versions.py
COPY hera/common/common.sh /project/common.sh
COPY --from=ssh_base /root/.ssh/* /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa-gerrit
RUN chmod +x /project/*.sh

ENTRYPOINT /project/entrypoint.sh

