FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/hanawire_test_base:k8s_10

RUN mkdir -p /project
COPY hera/common/common.sh /project/common.sh
COPY hera/ci/hanalite-releasepack/infrabox/hanawire_test/entrypoint.sh /project/entrypoint.sh
COPY hera/common/runTest.sh /project/runTest.sh
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py \
     common/ansible/tools/bdh_health_check.py \
     hera/ci/bdh-infra-tools/infrabox/CI_pre_check/pre_check.sh \
     /project/

RUN chmod +x /project/*.sh
RUN chmod +x /project/runTest.sh

ENTRYPOINT /project/pre_check.sh && /project/runTest.sh
