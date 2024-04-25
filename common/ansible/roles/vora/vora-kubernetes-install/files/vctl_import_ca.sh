#!/bin/bash
set -ex

./vctl login ${1} ${2} ${3} --password "${4}" --insecure
./vctl util http --header x-requested-with=Fetch --header Content-Type=application/json --header X-Datahub-Tenant=${2} --header X-Datahub-User=${3} -X PUT /app/datahub-app-connection/certificates --data "{\"cdata\":\"$(sed 's/$/\\n/' ${5} |tr -d '\n')\",\"filename\":\"docker_ssl_ca.crt\"}"
