FROM di-dev-cicd-docker.int.repositories.cloud.sap/bdh-infra-tools/alpine_log_collection_base:0.5

COPY hera/ci/hanalite-releasepack/infrabox/log_combine/entrypoint.sh \
     hera/ci/hanalite-releasepack/infrabox/log_combine/log_combine.py \
     hera/ci/hanalite-releasepack/infrabox/job_report/send_job_report.py \
    /
COPY common/script/python/send_mail.py /send_mail.py
COPY hera/ci/hanalite-releasepack/infrabox/job_report/config_*.json /
COPY hera/ci/hanalite-releasepack/infrabox/job_report/normal_job_time_cost.json /normal_job_time_cost.json
COPY hera/ci/hanalite-releasepack/infrabox/job_report/send_notification.py /send_notification.py
COPY common/script/python/slacklib.py /slacklib.py

RUN chmod +x /*.sh  /*.py

ENTRYPOINT /entrypoint.sh