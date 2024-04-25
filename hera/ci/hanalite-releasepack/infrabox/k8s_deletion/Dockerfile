FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/python3_slim_base:0.1

RUN mkdir -p /project
COPY hera/ci/hanalite-releasepack/infrabox/k8s_deletion/entrypoint.sh /project/entrypoint.sh
COPY hera/ci/hanalite-releasepack/infrabox/k8s_deletion/reserve_cluster.py /project/reserve_cluster.py
RUN chmod +x /project/entrypoint.sh

ENTRYPOINT /project/entrypoint.sh
