#!/bin/bash

set -e

HOSTNAME=$1

openssl genrsa -out rsa_private.key 2048
openssl pkcs8 -topk8 -inform PEM -in rsa_private.key -outform pem -nocrypt -out rsa_private_pkcs8.pem
openssl req -new -out CertRequest.csr -key rsa_private.key -subj "/C=DE/L=WDF/O=SAP/OU=bigdata/CN=${HOSTNAME}"

SERVER_CRT=$(curl --cacert ./ca.crt --cert ./all.pem -X POST \
  https://getcerts.wdf.global.corp.sap/pgwy/eui/sapnetca-esx \
  -H 'cache-control: no-cache' \
  -H 'content-type: application/x-www-form-urlencoded' \
  --data-urlencode 'certencoding=x509' \
  --data-urlencode "pkcs10=$(<CertRequest.csr)" | grep \"response | awk -F \" '{print $6}')

echo "" > server.crt
echo "-----BEGIN CERTIFICATE-----" >> server.crt
echo $SERVER_CRT >> server.crt
echo "-----END CERTIFICATE-----" >> server.crt

