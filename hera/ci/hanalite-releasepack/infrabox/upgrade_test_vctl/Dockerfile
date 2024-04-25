FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_upgrade_test_vctl:0.2

RUN mkdir -p /project
COPY hera/ci/hanalite-releasepack/infrabox/upgrade_test_vctl/vctl-start-app.py /project/vctl-start-app.py
COPY hera/common/common.sh /project/common.sh
COPY hera/ci/hanalite-releasepack/infrabox/upgrade_test_vctl/entrypoint.sh /project/entrypoint.sh

WORKDIR /project
RUN chmod +x /project/*.sh

ENTRYPOINT /project/entrypoint.sh
