FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/python3_slim_base:0.1

COPY hera/ci/hanalite-releasepack/infrabox/k8s_upgrade /project/k8s_upgrade
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py \
     common/ansible/tools/bdh_health_check.py \
     hera/ci/bdh-infra-tools/infrabox/CI_pre_check/pre_check.sh \
     /project/

RUN chmod +x /project/k8s_upgrade/*
RUN chmod +x /project/*

ENTRYPOINT /project/pre_check.sh && /project/k8s_upgrade/entrypoint.sh
