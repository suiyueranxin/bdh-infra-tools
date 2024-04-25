FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_python_with_kc:kc1.13.8

RUN mkdir -p /project
RUN  rm -rf /infrabox/context
COPY hera/ci/hanalite-releasepack/infrabox/slcb_test/entrypoint.py /project/entrypoint.py
COPY hera/ci/hanalite-releasepack/infrabox/slcb_test/slcb_validation.json /project/slcb_validation.json

ENTRYPOINT [ "python", "/project/entrypoint.py" ]
