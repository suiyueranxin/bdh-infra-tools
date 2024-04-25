FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/vflow_base

RUN mkdir -p /project

COPY hera/ci/hanalite-releasepack/infrabox/get_component_version/entrypoint.sh /project/entrypoint.sh
COPY common/ansible/tools/get_component_version.py /project/get_component_version.py
COPY hera/env/id_rsa hera/env/id_rsa.pub hera/env/known_hosts /root/.ssh/

RUN chmod +x /project/*.sh
RUN chmod 600 /root/.ssh/id_rsa

ENTRYPOINT /project/entrypoint.sh
