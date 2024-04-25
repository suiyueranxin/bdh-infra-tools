FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/pylint_check_base:0.1

COPY pylint_check/entrypoint.sh /project/entrypoint.sh
RUN chmod +x /project/entrypoint.sh

ENTRYPOINT /project/entrypoint.sh
