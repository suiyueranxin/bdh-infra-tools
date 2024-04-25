ARG PLATFORM=gke
FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_vsystem_test_with_docker_${PLATFORM}:go1.13.3_k8s10

RUN mkdir -p /project && \
    mkdir -p /go/src/github.wdf.sap.corp/velocity

COPY hera/ci/hanalite-releasepack/infrabox/vsystem_api_test/entrypoint.sh /project/entrypoint.sh
COPY hera/ci/hanalite-releasepack/infrabox/vsystem_api_test/check_vsystem_result.py /project/check_vsystem_result.py
COPY hera/ci/hanalite-releasepack/infrabox/vsystem_api_test/config.json /project/config.json
COPY hera/common/common.sh /project/common.sh
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py \
     common/ansible/tools/bdh_health_check.py \
     hera/ci/bdh-infra-tools/infrabox/CI_pre_check/pre_check.sh \
     /project/

RUN chmod +x /project/*.sh

ENV GOROOT=/usr/local/go
ENV GOPATH=/go

ENTRYPOINT /project/pre_check.sh && /project/entrypoint.sh

