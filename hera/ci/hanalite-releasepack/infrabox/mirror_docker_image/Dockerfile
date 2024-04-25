ARG BUILD_VERSION
FROM di-dev-cicd-v2.int.repositories.cloud.sap/infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:${BUILD_VERSION} as installer

ADD hera/ci/hanalite-releasepack/infrabox/mirror_docker_image/image_list /image_list
RUN /new_installer/dhinstaller image list --type target -r public.int.repositories.cloud.sap -s /new_installer/stack.yaml >> /image_list


#-----------
FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/build-and-push-images-base-with-latest-skopeo:0.0.01

ENV http_proxy= \
    https_proxy=

COPY --from=installer /image_list project/image_list

ARG INFRABOX_BUILD_NUMBER
ARG SCRIPT_WORKSPACE=fulcrum

ENV DH_VERSION=${BUILD_VERSION}

COPY ${SCRIPT_WORKSPACE}/script/bash/docker_start.sh /docker_start.sh
COPY common/ansible/tools/update_docker_daemon.py /ansible/tools/

COPY common/ansible/tools/generate_image_names.py /project/dhaas_mirror.py
COPY common/ansible/tools/mirror_docker_image_by_skopeo.sh /project/entrypoint.sh
COPY hera/ci/hanalite-releasepack/infrabox/mirror_docker_image/clone_repo.sh /project/clone_repo.sh
COPY common/ansible/tools/pull_and_push_docker_image.sh /project/pull_and_push_docker_image.sh

RUN chmod +x /docker_start.sh && \
    chmod +x /project/* 

CMD /docker_start.sh && /project/clone_repo.sh && /project/entrypoint.sh on_cloud
