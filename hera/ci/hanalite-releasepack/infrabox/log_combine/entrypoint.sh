#!/bin/bash
set -x
python /log_combine.py
cd /infrabox/upload/archive/
rm -f /infrabox/upload/archive/log_combine/combined.csv
tar -zcvf k8s_vora_log_combined.tar.gz log_combine
mv k8s_vora_log_combined.tar.gz /infrabox/upload/archive/
rm -rf /infrabox/upload/archive/log_combine