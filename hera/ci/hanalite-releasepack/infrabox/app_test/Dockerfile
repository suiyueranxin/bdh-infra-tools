FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:1.0 AS ssh_base
FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/app_test_base:node14_k8s10

RUN mkdir -p /project
COPY hera/ci/hanalite-releasepack/infrabox/app_test/entrypoint.sh /project/entrypoint.sh
COPY hera/ci/hanalite-releasepack/infrabox/app_test/prepare_app_test.sh /project/prepare_app_test.sh
COPY hera/ci/hanalite-releasepack/infrabox/app_test/run_test.sh /project/run_test.sh
COPY hera/common/runTest.sh /project/runTest.sh
COPY hera/common/common.sh /project/common.sh
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py \
     common/ansible/tools/bdh_health_check.py \
     hera/ci/bdh-infra-tools/infrabox/CI_pre_check/pre_check.sh \
     /project/
COPY --from=ssh_base /root/.ssh/* /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa-gerrit
RUN chmod +x /project/*.sh /project/prepare_app_test.sh /project/run_test.sh /project/runTest.sh

ENTRYPOINT /project/pre_check.sh && /project/entrypoint.sh
