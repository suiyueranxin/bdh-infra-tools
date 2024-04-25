#!/bin/bash

set -ex

BASE_FOLDER=$(pwd)

#write out current crontab
set +e
crontab -l > tmp_cron
set -e
#echo new cron into cron file
echo "0 22 * * 0,1,2,3,4 ${BASE_FOLDER}/start_job.sh" >> tmp_cron
echo "0 22 * * 0,1,2,3,4 ${BASE_FOLDER}/start_job_debug.sh" >> tmp_cron
echo "0 22 * * 0,1,2,3,4 ${BASE_FOLDER}/start_job_stable.sh" >> tmp_cron
echo "0 22 * * 0,1,2,3,4 ${BASE_FOLDER}/start_job_stable_debug.sh" >> tmp_cron
#
#install new cron file
crontab tmp_cron
rm tmp_cron

