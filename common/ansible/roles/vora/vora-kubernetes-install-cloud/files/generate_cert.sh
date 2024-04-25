#!/bin/bash

set -e


mkdir -p deployment/certs

cat crt.pem > deployment/certs/vora.conf.secop.tlsconfig.truststore
cat key.pem > deployment/certs/vora.conf.secop.tlsconfig.keystore
openssl rsa -outform pkcs1 -in key.pem -out rsa_private.key
openssl x509 -pubkey -noout -in crt.pem > deployment/certs/vora.conf.secop.jwtiss.truststore
cat rsa_private.key > deployment/certs/vora.conf.secop.jwtiss.keystore

