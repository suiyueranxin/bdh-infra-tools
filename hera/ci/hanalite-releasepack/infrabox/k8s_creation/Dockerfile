FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/python3_slim_base_conn:0.2

RUN mkdir -p /project/default
ARG GITHUB_BASE_URL
ENV GITHUB_BASE_URL=$GITHUB_BASE_URL
COPY hera/ci/hanalite-releasepack/infrabox/k8s_creation/create_k8s.py /project/create_k8s.py
COPY hera/ci/hanalite-releasepack/infrabox/k8s_creation/entrypoint.sh /project/entrypoint.sh
COPY hera/ci/hanalite-releasepack/infrabox/k8s_creation/add_white_list.yaml /project/add_white_list.yaml
COPY hera/ci/hanalite-releasepack/infrabox/k8s_creation/debug_di_setup.sh /project/debug_di_setup.sh
COPY common/ansible/tools/get_component_version.py /project/get_component_version.py
COPY common/ansible/tools/list_component_versions.py /project/list_component_versions.py

COPY hera/common/common.sh /project/common.sh
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py /project/six.py
COPY hera/ci/hanalite-releasepack/infrabox/k8s_creation/clone_repo.sh /project/clone_repo.sh
COPY common/ansible/tools/bdh_health_check.py /project/bdh_health_check.py
COPY common/ansible/tools/create_connection.py /project/create_connection.py
COPY common/ansible/tools/get_cloud_credentials.py /project/get_cloud_credentials.py


RUN chmod +x /project/*.sh

ENTRYPOINT /project/clone_repo.sh && /project/entrypoint.sh
