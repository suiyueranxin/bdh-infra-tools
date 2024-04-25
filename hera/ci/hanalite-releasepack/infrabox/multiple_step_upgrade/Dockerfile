FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_ssh_base:1.0 AS ssh_base

FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/milestone-val:base-0.1

ADD hera/ci/hanalite-releasepack/infrabox/multiple_step_upgrade/entrypoint.py /
ADD hera/ci/hanalite-releasepack/infrabox/multiple_step_upgrade/assemble.py /
ADD hera/ci/hanalite-releasepack/infrabox/multiple_step_upgrade/database /database

COPY --from=ssh_base /root/.ssh/* /root/.ssh/
RUN chmod 600 /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa-gerrit

ENTRYPOINT [ "python", "/entrypoint.py" ]
