FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build_and_push_images_with_kc:kc1.13.8_pyclient10.0.1

ARG SCRIPT_WORKSPACE=fulcrum
ARG ANSIBLE_WORKSPACE=common

ENV http_proxy= \
    https_proxy=

COPY ${ANSIBLE_WORKSPACE}/ansible /ansible
COPY ${SCRIPT_WORKSPACE}/script/bash/docker_start.sh /docker_start.sh
COPY hera/ci/hanalite-releasepack/infrabox/hanalite_dqp_test/entrypoint.sh /entrypoint.sh
COPY hera/ci/bdh-infra-tools/infrabox/service_check/junit_xml  /project/junit_xml
COPY hera/ci/bdh-infra-tools/infrabox/service_check/six.py \
     common/ansible/tools/bdh_health_check.py \
     hera/ci/bdh-infra-tools/infrabox/CI_pre_check/pre_check.sh \
     /project/

ARG INTERNAL_DOCKER_REGISTRY_DOMAIN_NAME
ARG INTERNAL_DOCKER_REGISTRY_PORT

RUN openssl s_client -connect ${INTERNAL_DOCKER_REGISTRY_DOMAIN_NAME}:${INTERNAL_DOCKER_REGISTRY_PORT} -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM | tee /usr/local/share/ca-certificates/${INTERNAL_DOCKER_REGISTRY_DOMAIN_NAME}.crt
RUN update-ca-certificates

RUN  chmod +x /docker_start.sh && \
     chmod +x /entrypoint.sh && \
     chmod +x /project/*.sh

WORKDIR /

ENTRYPOINT /project/pre_check.sh && /docker_start.sh && /entrypoint.sh
