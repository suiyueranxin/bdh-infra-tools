FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_generator_base

RUN mkdir -p /project
COPY hera/ci/bdh-infra-tools/infrabox/generator/* /project/
COPY hera/tools/utils/get_latest_commit_id.sh /project/get_latest_commit_id.sh
COPY hera/common/common.sh /project/common.sh
COPY common/ansible/tools/get_component_version.py /project/get_component_version.py
COPY common/ansible/tools/list_component_versions.py /project/list_component_versions.py
COPY hera/env/id_rsa hera/env/id_rsa.pub hera/env/known_hosts hera/env/config /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa && chmod 600 /root/.ssh/config
RUN chmod +x /project/*

ENTRYPOINT /project/entrypoint.sh
