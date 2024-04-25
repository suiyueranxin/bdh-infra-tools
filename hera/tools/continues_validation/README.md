# Hanalite-releasepack project continues validation tool
1.  Preparation
    You need prepare a RedHat(yum installed) machine(Monsoon is preferred).
2.  Detail
    Execute add_crontab.sh to create a cron job on the machine(22:00 everyday), then the job will fetch the newest hanalite-releasepack project, trigger infrabox continues validation framework to run build/install/test jobs, then the result will be returned via email notification.
3.  Job deploy machine
    Now the nightly job is deployed on machine: mo-61fb40313.mo.sap.corp, if you want to take a look, please use the ansible id_rsa file to logon to the machine.
