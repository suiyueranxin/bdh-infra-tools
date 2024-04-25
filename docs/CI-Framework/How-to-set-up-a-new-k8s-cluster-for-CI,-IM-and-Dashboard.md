# Set up k8s cluster
## Install ansible
Follow the [install guide](https://docs.ansible.com/ansible/2.8/installation_guide/intro_installation.html#intro-installation-guide) to complete the installation. The ansible version should >= 2.8

## Run ansible script
- Clone [bdh-infrastructure-manager](https://github.wdf.sap.corp/bdh/bdh-infrastructure-manager.git) to local
- Change the work directory to 
```
ansible-playbook -i ansible/tools/..//tools/..//inventories/monsoon_hosts /ansible/tools/..//tools/..//playbooks/cloud/monsoon/create-monsoon-cluster.yml --extra-vars '{"security_json_file":"/aws_credentials.txt","monsoon_region":"europe","monsoon_zone":"rot_1","master_image":"RHEL7-x86_64","worker_image":"RHEL7-x86_64","master_instance_type":"extralarge_8_16","worker_instance_type":"extralarge_8_16","monsoon_volume_size":200,"number_of_workers":3,"master_name":"lily-ke-20191204-075536064-k8svora-master","worker_name_prefix":"lily-ke-20191204-075536064-k8svora-worker","k8s_version":"1.13.6","installer_workspace":"/var","enable_authentication":"no","user_email":"lily.ke@sap.com","project_name":"k8svora","period":"16","description":"CI cluster","gcloud_instance_name":"lily-ke-20191204-075536064-k8svora","skip_vsystem_assembly":"yes"}' -v
```

```
ansible-playbook -i ansible/tools/..//tools/..//inventories/monsoon_hosts /ansible/tools/..//tools/..//playbooks/cloud/monsoon/monsoon-extend-volume.yml --extra-vars '{"security_json_file":"/aws_credentials.txt","monsoon_region":"europe","monsoon_zone":"rot_1","master_image":"RHEL7-x86_64","worker_image":"RHEL7-x86_64","master_instance_type":"extralarge_8_16","worker_instance_type":"extralarge_8_16","monsoon_volume_size":200,"number_of_workers":3,"master_name":"lily-ke-20191204-075536064-k8svora-master","worker_name_prefix":"lily-ke-20191204-075536064-k8svora-worker","k8s_version":"1.13.6","installer_workspace":"/var","enable_authentication":"no","user_email":"lily.ke@sap.com","project_name":"k8svora","period":"16","description":"CI cluster","gcloud_instance_name":"lily-ke-20191204-075536064-k8svora","skip_vsystem_assembly":"yes"}' -v
```
```
ansible-playbook -i ansible/tools/..//tools/..//inventories/monsoon_hosts /ansible/tools/..//tools/..//playbooks/k8s/install-k8s.yml --extra-vars '{"security_json_file":"/aws_credentials.txt","monsoon_region":"europe","monsoon_zone":"rot_1","master_image":"RHEL7-x86_64","worker_image":"RHEL7-x86_64","master_instance_type":"extralarge_8_16","worker_instance_type":"extralarge_8_16","monsoon_volume_size":200,"number_of_workers":3,"master_name":"lily-ke-20191204-075536064-k8svora-master","worker_name_prefix":"lily-ke-20191204-075536064-k8svora-worker","k8s_version":"1.13.6","installer_workspace":"/var","enable_authentication":"no","user_email":"lily.ke@sap.com","project_name":"k8svora","period":"16","description":"MILESTONE_VALIDATION MONSOON https://infrabox.datahub.only.sap/dashboard/#/project/milestone-validation/build/905/1","gcloud_instance_name":"lily-ke-20191204-075536064-k8svora","skip_vsystem_assembly":"yes"}' -v
```
- Save the admin.conf file

# Set up services and cron jobs
## Dashboard services
## CI services
## IM Services
