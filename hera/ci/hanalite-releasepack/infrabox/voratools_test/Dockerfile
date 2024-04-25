FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_python_with_kc:kc1.13.8_k8s10

RUN mkdir -p /project

COPY hera/ci/hanalite-releasepack/infrabox/voratools_test/entrypoint.sh  /project/entrypoint.sh
COPY hera/tools/utils/check_voratools_status.py   /project/check_voratools_status.py
COPY hera/common/common.sh /project/common.sh
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py \
     common/ansible/tools/bdh_health_check.py \
     hera/ci/bdh-infra-tools/infrabox/CI_pre_check/pre_check.sh \
     /project/

RUN chmod +x /project/*.sh

ENTRYPOINT /project/pre_check.sh && /project/entrypoint.sh

