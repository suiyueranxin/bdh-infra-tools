FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:1.0 AS ssh_base
FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_check_test_metadata:1.1

COPY common/script/python/get-full-product-stack/docker_pull.py /project/docker_pull.py
COPY hera/common/common.sh /project/common.sh
COPY hera/ci/hanalite-releasepack/infrabox/parse_dis_test_metadata/* /project/

COPY --from=ssh_base /root/.ssh/* /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa-gerrit

RUN mkdir -p /project/dis_metadata

RUN chmod +x /project/*.sh
WORKDIR /project
ENTRYPOINT ["/bin/bash", "/project/entrypoint.sh"]