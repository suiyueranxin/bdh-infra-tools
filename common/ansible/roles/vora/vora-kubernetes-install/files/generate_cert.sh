#!/bin/bash

set -e

HOSTNAME=$1
NAMESPACE=$2

mkdir -p cert_generation_tmp

pushd cert_generation_tmp
cp ../ca.crt ./ca.crt
cp ../all.pem ./all.pem

openssl genrsa -out rsa_private.key 2048
openssl dhparam -out dh.pem 2048
openssl pkcs8 -topk8 -inform PEM -in rsa_private.key -outform pem -nocrypt -out rsa_private_pkcs8.pem
if [ -z $NAMESPACE ]; then
  openssl req -new -out CertRequest.csr -key rsa_private.key -subj "/C=DE/L=WDF/O=SAP/OU=bigdata/CN=${HOSTNAME}"
else
    openssl req -new -out CertRequest.csr -key rsa_private.key -subj "/C=DE/L=WDF/O=SAP/OU=bigdata/CN=${HOSTNAME}" -reqexts SAN -config <(cat /etc/ssl/openssl.cnf <(printf "[SAN]\nsubjectAltName=DNS:${HOSTNAME},DNS:uaa,DNS:*.uaa,DNS:uaa.${NAMESPACE},DNS:*.uaa.${NAMESPACE},DNS:*.${NAMESPACE}"))
fi

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

popd

mkdir -p deployment/certs

if [ -z $NAMESPACE ]; then
  cp cert_generation_tmp/ca.crt deployment/certs/ca.crt
  cat cert_generation_tmp/server.crt > deployment/certs/vora.conf.secop.tlsconfig.truststore
  cat cert_generation_tmp/rsa_private_pkcs8.pem > deployment/certs/vora.conf.secop.tlsconfig.keystore
  openssl x509 -pubkey -noout -in cert_generation_tmp/server.crt > deployment/certs/vora.conf.secop.jwtiss.truststore
  cat cert_generation_tmp/rsa_private.key > deployment/certs/vora.conf.secop.jwtiss.keystore
else
  cat cert_generation_tmp/ca.crt > deployment/certs/vora.conf.secop.tlsconfig.ca-bundle
  cat cert_generation_tmp/server.crt > deployment/certs/vora.conf.secop.tlsconfig.truststore
  cat cert_generation_tmp/rsa_private_pkcs8.pem > deployment/certs/vora.conf.secop.tlsconfig.keystore
  openssl x509 -pubkey -noout -in cert_generation_tmp/server.crt > deployment/certs/vora.conf.secop.jwtiss.truststore
  cat cert_generation_tmp/rsa_private.key > deployment/certs/vora.conf.secop.jwtiss.keystore
  cat cert_generation_tmp/ca.crt > deployment/certs/vora.conf.secop.jwtiss.ca-bundle
  cat cert_generation_tmp/dh.pem > deployment/certs/vora.conf.secop.tlsconfig.keystore-dh
fi

rm -rf cert_generation_tmp
