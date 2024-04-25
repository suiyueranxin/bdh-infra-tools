FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:1.0 AS ssh_base

FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/vflow_with_kc:kc1.13.8_k8s10

ARG VIT_VERSION=0.5.0

RUN apk add coreutils
RUN mkdir -p /project && \
    apt-get install -y python3-pip && \ 
    pip3 install sap-datahub-vflow-vit=="${VIT_VERSION}" -i https://int.repositories.cloud.sap/artifactory/api/pypi/build-milestones-pypi/simple/ --trusted-host int.repositories.cloud.sap

COPY hera/common/common.sh /project/common.sh
COPY hera/ci/hanalite-releasepack/infrabox/vflow_components_test/entrypoint.sh /project/entrypoint.sh
COPY hera/ci/hanalite-releasepack/infrabox/vflow_components_test/check_vflow_result.py /project/check_vflow_result.py
COPY hera/env/id_rsa hera/env/id_rsa.pub hera/env/known_hosts /root/.ssh/
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py \
     common/ansible/tools/bdh_health_check.py \
     hera/ci/bdh-infra-tools/infrabox/CI_pre_check/pre_check.sh \
     /project/

RUN chmod +x /project/*.sh && chmod +x /project/check_vflow_result.py
COPY --from=ssh_base /root/.ssh/* /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa-gerrit


ENTRYPOINT /project/pre_check.sh && /project/entrypoint.sh
