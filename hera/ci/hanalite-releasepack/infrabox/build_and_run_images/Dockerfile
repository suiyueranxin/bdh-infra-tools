FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:2.0 AS ssh_base
FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_and_push_images_ubuntu_gsutil:0.1

ARG SCRIPT_WORKSPACE=fulcrum

ENV http_proxy= \
    https_proxy=

COPY ${SCRIPT_WORKSPACE}/script/bash/docker_start.sh /docker_start.sh
COPY hera/ci/hanalite-releasepack/infrabox/build_and_run_images/entrypoint.sh /entrypoint.sh
COPY hera/common/common.sh /project/common.sh
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py \
     common/ansible/tools/bdh_health_check.py \
     common/ansible/tools/update_docker_daemon.py \
     common/ansible/tools/create_connection.py \
     hera/ci/bdh-infra-tools/infrabox/CI_pre_check/pre_check.sh \
     /project/

COPY --from=ssh_base /root/.ssh/* /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa-gerrit

RUN  chmod +x /docker_start.sh && \
     chmod +x /entrypoint.sh && \
     chmod +x /project/*.sh

COPY hera/ci/hanalite-releasepack/infrabox/build_and_run_images/dis_create_tenant.py \
     hera/ci/hanalite-releasepack/infrabox/build_and_run_images/tools.py \
     hera/ci/hanalite-releasepack/infrabox/build_and_run_images/dis_delete_tenant.py /
     
RUN pip3 install cryptography

RUN  chmod +x /*.py
WORKDIR /

ENTRYPOINT /project/pre_check.sh && /docker_start.sh && /entrypoint.sh
