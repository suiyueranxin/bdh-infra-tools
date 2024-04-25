FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_python_with_dateutil:0.1

RUN mkdir -p /project
ADD hera/ci/hanalite-releasepack/infrabox/fetch-e2e-secrets/fetch.py /project/fetch.py
ADD hera/ci/hanalite-releasepack/infrabox/fetch-e2e-secrets/entrypoint.sh /project/entrypoint.sh

WORKDIR /project
RUN chmod +x /project/entrypoint.sh

ENTRYPOINT /project/entrypoint.sh