#!/bin/bash
set -x

BASE_FOLDER=$(dirname $0)
echo ${BASE_FOLDER}

python ${BASE_FOLDER}/send_daily_job_report.py False
