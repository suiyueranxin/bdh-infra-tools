## Update slcb version
### For milestone validation tests
Update slcb version in hanalite-releasepack on specific branch
- For example, on rel-3.3, update [SLC_BRIDGE_BASE_VERSION](https://git.wdf.sap.corp/plugins/gitiles/hanalite-releasepack/+/refs/heads/rel-3.3/images/com.sap.datahub.linuxx86_64/installer/Dockerfile#3)
### For the kubernetes cluster of IM
Update slcb version in [vora-kubernetes-install-cloud/defaults/main.yml](https://github.wdf.sap.corp/bdh/bdh-infrastructure-manager/blob/main/common/ansible/roles/vora/vora-kubernetes-install-cloud/defaults/main.yml#L142)
and [vora-kubernetes-install/defaults/main.yml](https://github.wdf.sap.corp/bdh/bdh-infrastructure-manager/blob/main/common/ansible/roles/vora/vora-kubernetes-install/defaults/main.yml#L69)