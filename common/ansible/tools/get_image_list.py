#!/usr/bin/python
# get image list
#
# the input file content would be like below
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.dsp.linuxx86_64/jupyter:0.1.48
# com.sap.datahub.linuxx86_64/nats:0.11.2-sap2
# com.sap.datahub.linuxx86_64/sles:15.0-sap-010
# com.sap.datahub.linuxx86_64/datahub-operator:2002.0.54
# com.sap.dsp.linuxx86_64/dsp-git-server-foss:1.4.21
# com.sap.datahub.linuxx86_64/hana:2002.0.4
# com.sap.mlf/tyom-suse-tf-1.14-py36-gpu:1.1.20
# com.sap.datahub.linuxx86_64/vsolution-golang:2002.0.19
# com.sap.datahub.linuxx86_64/vora-deployment-operator:3.0.16
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/uaa:2.7.89
# com.sap.datahub.linuxx86_64/auth-proxy:2.7.89
# com.sap.datahub.linuxx86_64/app-base:2002.0.14
# com.sap.datahub.linuxx86_64/sles:15.0-sap-010
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/security-operator:2.7.89
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/vora-dqp-textanalysis:3.0.16
# com.sap.datahub.linuxx86_64/prometheus:2.13.0-sap-002
# com.sap.dsp.linuxx86_64/dsp-git-server-sap:1.4.21
# com.sap.datahub.linuxx86_64/security-operator-init:2.7.89
# com.sap.datahub.linuxx86_64/vsolution-hana_replication:2002.0.19
# com.sap.datahub.linuxx86_64/sles:15.0-sap-010
# com.sap.datahub.linuxx86_64/vsystem-vrep-csi:2002.0.16
# com.sap.datahub.linuxx86_64/code-server:1911.0.1
# com.sap.dsp.linuxx86_64/ml-dm-app:1.0.13
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/vsystem:2002.0.16
# com.sap.datahub.linuxx86_64/vora-dqp:3.0.16
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/kube-state-metrics:1.7.2-sap-002
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.dsp.linuxx86_64/ml-scenario-manager:1.2002.4
# com.sap.datahub.linuxx86_64/vsolution-sapjvm:2002.0.19
# com.sap.datahub.linuxx86_64/vsolution-textanalysis:2002.0.19
# com.sap.datahub.linuxx86_64/vsystem-shared-ui:2003.0.1
# com.sap.dsp.linuxx86_64/sapautoml:0.6.11
# com.sap.datahub.linuxx86_64/app-base:2002.0.14
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/datahub-operator-installer-base:2002.0.54
# kaniko-project/executor:v0.13.0
# com.sap.datahub.linuxx86_64/flowagent-codegen:2002.0.9
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.bds.docker/storagegateway:2002.0.2
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/dq-integration:2002.0.2
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.mlf/tyom-suse-tf-1.15-py36-gpu:1.1.20
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/vsystem-module-loader:2002.0.16
# com.sap.datahub.linuxx86_64/vsystem-ui:2002.0.7
# com.sap.datahub.linuxx86_64/elasticsearch:7.1.0-sap-004
# com.sap.datahub.linuxx86_64/node-exporter:0.18.1-sap-002
# com.sap.dsp.linuxx86_64/dsp-content-docker:0.0.17
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/vsystem-auth:2002.0.16
# com.sap.datahub.linuxx86_64/flowagent-service:2002.0.9
# com.sap.datahub.linuxx86_64/vsystem-installer-configure:2002.0.16
# com.sap.datahub.linuxx86_64/vsystem-voraadapter:2002.0.15
# com.sap.dsp.linuxx86_64/automl:1.2002.2
# com.sap.datahub.linuxx86_64/vsolution-streaming:2002.0.19
# com.sap.datahub.linuxx86_64/kibana:7.1.0-sap-003
# com.sap.dsp.linuxx86_64/dsp-core-operators:0.6.11
# com.sap.dsp.linuxx86_64/ml-api:1.2002.4
# com.sap.datahub.linuxx86_64/vsystem-teardown:2002.0.16
# com.sap.mlf/tyom-suse-tf-2.0-py36-cpu:1.1.20
# com.sap.datahub.linuxx86_64/fluentd:1.6.3-sap-005
# com.sap.dsp.linuxx86_64/metrics-explorer:0.0.9
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.mlf/tyom-suse-pytorch-1.3-py36-cpu:1.1.10
# com.sap.datahub.linuxx86_64/vsystem-vrep:2002.0.16
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/app-data:2002.0.13
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/pushgateway:0.5.2-sap-008
# com.sap.datahub.linuxx86_64/vora-license-manager:2002.0.2
# com.sap.datahub.linuxx86_64/vora-tools:2003.0.1
# com.sap.datahub.linuxx86_64/grafana:5.4.2-sap-008
# com.sap.datahub.linuxx86_64/flowagent-operator:2002.0.9
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.mlf/tyom-suse-tf-1.14-py36-cpu:1.1.20
# com.sap.datahub.linuxx86_64/axino-service:3.0.3
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.dsp.linuxx86_64/ml-tracking:0.9.26
# com.sap.mlf/tyom-suse-tf-1.15-py36-cpu:1.1.20
# com.sap.mlf/tyom-suse-tf-2.0-py36-gpu:1.1.20
# com.sap.datahub.linuxx86_64/app-base:2002.0.14
# com.sap.datahub.linuxx86_64/vsystem-hana-init:2002.0.16
# kubernetes-helm/tiller:v2.11.0
# com.sap.mlf/tyom-suse-pytorch-1.3-py36-gpu:1.1.10
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.dsp.linuxx86_64/ml-dm-api:1.0.9
# consul:0.9.0
# com.sap.datahub.linuxx86_64/rbase:3.5.0-sap-005
# infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
# com.sap.datahub.linuxx86_64/spark-datasourcedist:2002.0.1

import sys
import os
# arg[1]: image list file that from Bridge image
# arg[2]: image list file that for skepo mirror
#         source_image_with_tag;target_image_with_tag
# arg[3]: SLC Bridge tool version
# arg[4]: private repo, used as target repository, must not end with '/'
slcb_version = sys.argv[3]
target = sys.argv[4]
slcb_package_suffix = "zip"

extra_images = [
    'com.sap.sl.cbpod/nginx-sidecar:'+slcb_version,
    'com.sap.sl.cbpod/slcbridgehead:'+slcb_version,
    'com.sap.sl.cbpod/slcbridgebase:'+slcb_version
]
output = []
with open(sys.argv[1]) as images_file:
    source_wdf='public.int.repositories.cloud.sap'
    for image in images_file:
        image = image.strip()
        if not image.startswith('infrabox'):
            line = "%s/%s;%s/%s\n" % (source_wdf, image, target, image)
            output.append(line)
        else:
            # image start with "infrabox" it should alread exist 
            # e.g: infrabox/hanalite-releasepack/com.sap.datahub.linuxx86_64/installer:build_14682
            pass
customed_binary = os.environ.get('USE_CUSTOMIZED_SLCB_BINARY', 'false')
with open(sys.argv[2], 'w') as f:
    for line in output:
        f.write(line)
    for image in extra_images:
        if customed_binary == 'false':
            f.write("%s/%s;%s/%s\n" % (source_wdf, image, target, image))
        else:
            source_reg = 'di-dev-cicd-v2.int.repositories.cloud.sap/slcb'
            f.write("%s/%s;%s/%s\n" % (source_reg, image, target, image))
