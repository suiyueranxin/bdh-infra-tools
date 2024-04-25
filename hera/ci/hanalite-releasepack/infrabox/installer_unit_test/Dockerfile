FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/installer_unit_test_base:latest

RUN mkdir -p /project
COPY hera/common/common.sh /project/common.sh
COPY hera/ci/hanalite-releasepack/infrabox/installer_unit_test/entrypoint.sh /project/entrypoint.sh
COPY hera/env/id_rsa hera/env/id_rsa.pub hera/env/known_hosts /root/.ssh/
COPY common/ansible/tools/get_component_version.py /project/get_component_version.py
COPY common/ansible/tools/list_component_versions.py /project/list_component_versions.py

RUN chmod +x /project/*.sh && \
    chmod 600 /root/.ssh/id_rsa

ENTRYPOINT /project/entrypoint.sh
