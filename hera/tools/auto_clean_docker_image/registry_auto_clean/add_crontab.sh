#!/bin/bash

set -ex

BASE_FOLDER=$(pwd)

#write out current crontab
set +e
crontab -l > tmp_cron
set -e
#echo new cron into cron file
echo "0 0 * * 0 ${BASE_FOLDER}/auto_clean.sh" >> tmp_cron
#
#install new cron file
crontab tmp_cron
rm tmp_cron

