FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build-and-push-images-base:awscli_1_16

ENV http_proxy= \
    https_proxy=

COPY hera/ci/hanalite-releasepack/infrabox/delete_docker_image/entrypoint.sh /project/entrypoint.sh

RUN chmod +x /project/*

CMD /project/entrypoint.sh
