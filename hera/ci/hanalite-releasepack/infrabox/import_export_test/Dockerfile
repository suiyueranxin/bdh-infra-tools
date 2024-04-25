FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/import_export_test_base:with_docker_k8s10

COPY hera/common/common.sh /project/common.sh
COPY hera/tools/utils/check_import-export_status.py  /project/check_import-export_status.py
COPY hera/ci/hanalite-releasepack/infrabox/import_export_test/entrypoint.sh  /project/entrypoint.sh
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py \
     common/ansible/tools/bdh_health_check.py \
     hera/ci/bdh-infra-tools/infrabox/CI_pre_check/pre_check.sh \
     /project/

RUN chmod +x /project/*.sh

ENTRYPOINT /project/pre_check.sh && /project/entrypoint.sh
