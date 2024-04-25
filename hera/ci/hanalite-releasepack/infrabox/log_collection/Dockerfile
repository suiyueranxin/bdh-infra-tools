FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_log_collection_base:0.5
RUN mkdir -p /project

COPY hera/ci/hanalite-releasepack/infrabox/log_collection/entrypoint.sh \
     hera/ci/hanalite-releasepack/infrabox/log_collection/log_error_export.py \
     hera/ci/hanalite-releasepack/infrabox/log_collection/log_collection.py \
     hera/common/common.sh \
     hera/common/prometheus.py /project/

RUN chmod +x /project/*.sh /project/prometheus.py

ENTRYPOINT /project/entrypoint.sh
