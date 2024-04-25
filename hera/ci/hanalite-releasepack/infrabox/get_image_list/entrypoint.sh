#!/bin/bash
echo "## Start to copy image list to /infrabox/output"
mkdir -p /infrabox/output/
cp /image_list /infrabox/output/image_list
echo "## image_list"
sed -i "s/\${DH_VERSION}/${DH_VERSION}/g" /infrabox/output/image_list
sed -i "s/public.int.repositories.cloud.sap\/com.sap.datahub.linuxx86_64\/installer:${DH_VERSION}//g" /infrabox/output/image_list
cat /infrabox/output/image_list
echo "## Copy image list done !"
