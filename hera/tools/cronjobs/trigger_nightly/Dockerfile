FROM docker.wdf.sap.corp:51022/com.sap.datahub.linuxx86_64/hanalite-build:0.0.13

RUN apt-get update && \
    apt-get -y install python-pip && \
    pip install infraboxcli

COPY hera/tools/continues_validation/* /project/

COPY hera/env/id_rsa hera/env/id_rsa.pub hera/env/known_hosts /root/.ssh/

RUN chmod +x /project/*.sh
RUN chmod 600 /root/.ssh/id_rsa

ENTRYPOINT ["/project/start_job_with_odtem.sh", "DEV","MASTER"] 
