FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:1.0 AS ssh_base
FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_base:docker

ARG SCRIPT_WORKSPACE=fulcrum
RUN mkdir -p /project

COPY hera/ci/hanalite-releasepack/infrabox/build/entrypoint.sh \
     hera/ci/hanalite-releasepack/infrabox/build/settings.xml \
     common/ansible/tools/get_component_version.py \
     common/ansible/tools/get_image_list.py \
     common/ansible/tools/list_component_versions.py \
     hera/common/common.sh \
     /project/
COPY ${SCRIPT_WORKSPACE}/script/bash/docker_start.sh /docker_start.sh

COPY --from=ssh_base /root/.ssh/* /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa-gerrit
RUN chmod +x /project/*.sh && \
    chmod +x /docker_start.sh && \
    chmod +r /project/settings.xml

ENTRYPOINT /docker_start.sh && /project/entrypoint.sh

