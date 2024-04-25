FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_python_with_dateutil:0.1

RUN mkdir -p /project

ARG GITHUB_BASE_URL
ENV GITHUB_BASE_URL=$GITHUB_BASE_URL

COPY hera/ci/hanalite-releasepack/infrabox/job_report/send_job_report.py /project/send_job_report.py
COPY common/script/python/send_mail.py /project/send_mail.py
COPY hera/ci/hanalite-releasepack/infrabox/job_report/config_*.json /project/
COPY hera/ci/hanalite-releasepack/infrabox/job_report/normal_job_time_cost.json /project/normal_job_time_cost.json
COPY hera/ci/hanalite-releasepack/infrabox/job_report/entrypoint.sh /project/entrypoint.sh
COPY hera/ci/hanalite-releasepack/infrabox/job_report/send_notification.py /project/send_notification.py
COPY common/script/python/slacklib.py /project/slacklib.py

WORKDIR /project
RUN chmod +x /project/entrypoint.sh

ENTRYPOINT /project/entrypoint.sh
