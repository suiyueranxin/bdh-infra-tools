#!/bin/bash
CURRENT_ROOTDIR="$(cd "$(dirname "${BASH_SOURCE-$0}")" && pwd)"
set -euxo pipefail

NAMESPACE="test-installation-${INFRABOX_BUILD_NUMBER}" \

kubectl -n $NAMESPACE expose service vsystem --type NodePort --name=vsystem-ext
kubectl -n $NAMESPACE patch service vsystem-ext -p '{"spec": {"ports" : [{"name": "vsystem-ext", "port" : 8797}]}}'
kubectl -n $NAMESPACE annotate service vsystem-ext service.alpha.kubernetes.io/app-protocols='{"vsystem-ext":"HTTPS"}'

#gke_domain_name="edward-wang-20200803-053744601"
gke_domain_name=$(cat $(find /infrabox/inputs -mindepth 2 -maxdepth 2 -name k8s_cluster.txt))
gcloud_vsystem_domain_name="${gke_domain_name}-gke.infra.datahub.sapcloud.io"

mv /test/crt.pem /test/default_crt.pem
mv /test/key.pem /test/default_key.pem

BASE_URL="https://${GITHUB_OAUTH_TOKEN}@github.wdf.sap.corp/I310657/im_downloads/tree/master/secret/cert/data-hub-cert-update"

r_crt=1
r_key=1
count=1

while [ ${r_crt} -ne 0 ]||[ ${r_key} -ne 0 ]
do
    set +x
    curl  -k -Lo /test/crt.pem ${BASE_URL}"/crt.pem"
    r_crt=$?
    curl  -k -Lo /test/key.pem ${BASE_URL}"/key.pem"
    r_key=$?
    set -x
    count=$(($count + 1))

    if [ ${count} -gt 3 ]; then
        if [ ${r_crt} -ne 0 ]||[ ${r_key} -ne 0 ]; then
            echo "## [level=warning] Failed to obtain the certificate and still using the default certificate."
            cp /test/default_crt.pem /test/crt.pem
            cp /test/default_key.pem /test/key.pem
        fi
        break
    fi
    rm -f /test/*.pem
done

kubectl -n $NAMESPACE create secret tls vsystem-tls-certs --key /test/key.pem --cert /test/crt.pem

# replace gcloud_vsystem_domain_name
sed -i "s/gcloud_vsystem_domain_name/"$gcloud_vsystem_domain_name"/g" /test/gke_ingress.yaml 
kubectl create -n $NAMESPACE -f /test/gke_ingress.yaml 
sleep 180
kubectl get ingress vsystem --namespace=$NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
dns_ip=`kubectl get ingress vsystem -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'`

chmod +x /test/create_route53.py
python /test/create_route53.py CREATE $gcloud_vsystem_domain_name A "$dns_ip"
sleep 15

echo "## write env.sh with DI connection info"
cp $(find /infrabox/inputs -mindepth 2 -maxdepth 2 -name env.sh) /infrabox/output/env.sh
cat /env.sh >> /infrabox/output/env.sh

echo "export VSYSTEM_ENDPOINT=https://$gcloud_vsystem_domain_name" >> /infrabox/output/env.sh
echo "export NAMESPACE=test-installation-${INFRABOX_BUILD_NUMBER}" >> /infrabox/output/env.sh
echo "export VORA_SYSTEM_TENANT=system" >> /infrabox/output/env.sh
echo "export VORA_TENANT=default" >> /infrabox/output/env.sh
echo "export VORA_USERNAME=${DEFAULT_ADMIN_USERNAME}" >> /infrabox/output/env.sh
echo "export VORA_PASSWORD=${DEFAULT_ADMIN_PASSWORD}" >> /infrabox/output/env.sh
echo "export VORA_SYSTEM_TENANT_PASSWORD=${SYSTEM_PASSWORD}" >> /infrabox/output/env.sh

chmod +x /infrabox/output/env.sh
cp /infrabox/output/env.sh /infrabox/upload/archive/env.sh
