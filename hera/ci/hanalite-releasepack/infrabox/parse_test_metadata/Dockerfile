FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:2.0 AS ssh_base
FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_check_test_metadata:1.2

COPY common/ansible/tools/get_component_version.py /project/get_component_version.py
COPY common/ansible/tools/list_component_versions.py /project/list_component_versions.py
COPY common/script/python/get-full-product-stack/docker_pull.py /project/docker_pull.py
COPY hera/common/common.sh /project/common.sh
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py /project/
COPY hera/ci/hanalite-releasepack/infrabox/parse_test_metadata/* /project/

COPY --from=ssh_base /root/.ssh/* /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa-gerrit

RUN mkdir -p /project/metadata

RUN chmod +x /project/*.sh
WORKDIR /project
ENTRYPOINT ["/bin/bash", "/project/entrypoint.sh"]