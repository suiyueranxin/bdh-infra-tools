ARG BUILD_VERSION

FROM di-dev-cicd-v2.int.repositories.cloud.sap/infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:${BUILD_VERSION} as installer

ARG BUILD_VERSION

ADD hera/ci/hanalite-releasepack/infrabox/mirror_docker_image/image_list /image_list

RUN /new_installer/dhinstaller image list --type target -r public.int.repositories.cloud.sap -s /new_installer/stack.yaml >> /image_list

ENV DH_VERSION=${BUILD_VERSION}

COPY hera/ci/hanalite-releasepack/infrabox/get_image_list/entrypoint.sh /entrypoint.sh

CMD /entrypoint.sh
