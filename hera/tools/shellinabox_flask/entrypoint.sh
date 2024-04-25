#!/bin/bash

################################################################################
# Starting docker service takes few seconds so we need to wait until it is done
# It is a must have for minikube with vm-driver=none. Otherwise there are no
# nodes available for k8s minikube cluster: "no nodes available to schedule pods"
################################################################################

echo "## Starting docker daemon"

nohup dockerd &

python /app/app.py

