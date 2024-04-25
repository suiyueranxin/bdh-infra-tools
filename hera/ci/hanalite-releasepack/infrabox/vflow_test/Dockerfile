FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_vflow_test_with_kc:kc1.13.8_k8s10

RUN mkdir -p /project

ARG VIT_VERSION=0.5.0

RUN apk add coreutils
COPY hera/common/common.sh /project/common.sh
COPY hera/ci/hanalite-releasepack/infrabox/vflow_test/entrypoint.sh /project/entrypoint.sh
COPY hera/ci/hanalite-releasepack/infrabox/vflow_test/check_vflow_result.py /project/check_vflow_result.py
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py \
     common/ansible/tools/bdh_health_check.py \
     hera/ci/bdh-infra-tools/infrabox/CI_pre_check/pre_check.sh \
     /project/

RUN chmod +x /project/*.sh && chmod +x /project/check_vflow_result.py && \
    apk add --no-cache --update libc6-compat > /dev/null && \
    pip3 install sap-datahub-vflow-vit=="${VIT_VERSION}" -i https://int.repositories.cloud.sap/artifactory/api/pypi/build-milestones-pypi/simple/ --trusted-host int.repositories.cloud.sap

ENTRYPOINT /project/pre_check.sh && /project/entrypoint.sh
