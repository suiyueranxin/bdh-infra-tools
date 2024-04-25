FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_python_base:latest

RUN mkdir -p /project

COPY hera/ci/hanalite-releasepack/infrabox/process_callback/entrypoint.py /project/entrypoint.py

CMD python /project/entrypoint.py
