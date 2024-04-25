#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
import json
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.containerregistry.models import Sku,StorageAccountParameters
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.containerservice.models import ContainerServiceOrchestratorProfile,ContainerServiceAgentPoolProfile,ContainerService,ContainerServiceMasterProfile,ContainerServiceSshConfiguration,ContainerServiceSshPublicKey,ContainerServiceLinuxProfile,ContainerServiceServicePrincipalProfile
from ansible.module_utils.basic import AnsibleModule
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import PublicIPAddressDnsSettings

def timedStr(mesg):
    return '[' + str(time.strftime('%Y%m%d.%H%M%S')) + '] ' + mesg

class Log:
    ERROR = 0
    WARN = 1
    INFO = 2
    DEBUG = 3
    TRACE = 4
    __level = ERROR
    __loggers = []

    def __init__(self, level, loggers):
        self.__level = level
        self.__loggers = loggers

    def error(self, msg):
        if self.__level >= Log.ERROR:
            self.log(msg)

    def info(self, msg):
        if self.__level >= Log.INFO:
            self.log(msg)

    def log(self, msg):
        for logger in self.__loggers:
            if logger == 'sys.stdout':
                print timedStr(str(msg))
            else:
                fw = open(logger, 'a+')
                fw.write(timedStr(str(msg) + '\n'))

class AzureUtils:
    def __init__(self, module):
        self.resource_group_action = module.params["resource_group_action"]
        self.location = module.params["location"]
        self.resource_group_name = module.params["resource_group_name"]
        self.registry_name = module.params["registry_name"]
        self.sku = module.params["sku"]
        self.admin_user_enabled = module.params["admin_user_enabled"]
        self.container_service_name = module.params["container_service_name"]
        self.cluster_name = module.params["cluster_name"]
        self.master_dns_prefix = module.params["master_dns_prefix"]
        self.master_type = module.params["master_type"]
        self.master_count = module.params["master_count"]
        self.sshpublickey = module.params["sshpublickey"]
        self.linux_user = module.params["linux_user"]
        self.agent_name = module.params["agent_name"]
        self.agent_dns_prefix = module.params["agent_dns_prefix"]
        self.agent_type = module.params["agent_type"]
        self.agent_count = module.params["agent_count"]
        self.agent_os_type = module.params["agent_os_type"]
        self.storage_accounts_name = module.params["storage_accounts_name"]
        self.storage_accounts_sku = module.params["storage_accounts_sku"]
        self.storage_accounts_kind = module.params["storage_accounts_kind"]
        self.public_ip_address_name = module.params["public_ip_address_name"]
        self.domain_name_label = module.params["domain_name_label"]
        self.subscription_id = module.params["subscription_id"]
        self.client_id = module.params["client_id"]
        self.client_secret = module.params["client_secret"]
        self.tenant = module.params["tenant"]

        self._logger_name = 'AzureUtils'
        self.logfile = Log(Log.INFO, ['/tmp/ansible_log.txt'])
        self.logout = Log(Log.INFO, ['sys.stdout'])
        self.credentials = ServicePrincipalCredentials(client_id=self.client_id, secret=self.client_secret, tenant=self.tenant)
        
    def create_public_ip_address(self):
        self.logfile.info('create public ip address ...')
        client = NetworkManagementClient(self.credentials, self.subscription_id)
        dnsset = PublicIPAddressDnsSettings(self.domain_name_label)
        parameters = {'location':'westeurope','public_ip_allocation_method':'Static','public_ip_address_version':'IPv4','dns_settings':dnsset}
        return self.create_public_ip_address_json(client.public_ip_addresses.create_or_update(self.resource_group_name, self.public_ip_address_name, parameters))

    def create_resource_group(self):
        self.logfile.info('create resource group ...')
        client = ResourceManagementClient(self.credentials, self.subscription_id)
        resource_group_params = {'location':self.location}
        # Create Resource group
        return self.create_resource_group_result_json(client.resource_groups.create_or_update(self.resource_group_name, resource_group_params))

    def delete_resource_group(self):
        client = ResourceManagementClient(self.credentials, self.subscription_id)
        # Delete Resource group
        return client.resource_groups.delete(self.resource_group_name)

    def create_storage_accounts(self):
        client = StorageManagementClient(self.credentials, self.subscription_id)
        objStorageSku = Sku(self.storage_accounts_sku)
        parameters = {'location':self.location,'sku':objStorageSku,'kind':self.storage_accounts_kind}
        # create storage accounts
        return self.create_storage_accounts_result_json(client.storage_accounts.create(self.resource_group_name, self.storage_accounts_name, parameters))

    def create_storage_accounts_result_json(self, group):
        storage_accounts_result = {}
        storage_accounts_result["storage_accounts_name"] = group.result().name
        storage_accounts_result["storage_accounts_id"] = group.result().id
        storage_accounts_result["storage_accounts_location"] = group.result().location
        return storage_accounts_result

    def get_keys(self):
        client = StorageManagementClient(self.credentials, self.subscription_id)
        return client.storage_accounts.list_keys(self.resource_group_name, self.storage_accounts_name)

    def create_container_registry(self, access_key):
        self.logfile.info('create container registry ...')
        client = ContainerRegistryManagementClient(self.credentials, self.subscription_id)
        resource_group_params = {'location':self.location}
        objSku = Sku(self.sku)
        storage_account = StorageAccountParameters(self.storage_accounts_name, access_key)
        registry = {'location':self.location,'sku':objSku,'admin_user_enabled':self.admin_user_enabled,'storage_account':storage_account}
        #create container registry
        return self.create_container_registry_result_json(client.registries.create(self.resource_group_name, self.registry_name, registry))

    def delete_container_registry(self):
        self.logfile.info('delete container registry ...')
        client = ContainerRegistryManagementClient(self.credentials, self.subscription_id)
        #delete container registry
        return client.registries.delete(self.resource_group_name, self.registry_name)

    def create_container_service(self):
        self.logfile.info('create container service ...')
        client = ContainerServiceClient(self.credentials, self.subscription_id)
        orchestrator_profile = ContainerServiceOrchestratorProfile(self.cluster_name)
        master_profile = ContainerServiceMasterProfile(self.master_dns_prefix, self.master_type, self.master_count, None, None, None, None)
        ssh = ContainerServiceSshConfiguration([ContainerServiceSshPublicKey(self.sshpublickey)])
        linux_profile = ContainerServiceLinuxProfile(self.linux_user, ssh)
        agent_pool_profiles = [ContainerServiceAgentPoolProfile(self.agent_name,self.agent_type,count = self.agent_count,os_disk_size_gb=None, dns_prefix=self.agent_dns_prefix, ports=None, storage_profile=None, vnet_subnet_id=None, os_type=self.agent_os_type)]
        service_principal_profile = ContainerServiceServicePrincipalProfile(self.client_id, self.client_secret)
        parameters = {'location':'westeurope','orchestrator_profile':orchestrator_profile,'master_profile':master_profile,'linux_profile':linux_profile,'agent_pool_profiles':agent_pool_profiles,'service_principal_profile':service_principal_profile}
        #create container service
        return self.create_container_service_result_json(client.container_services.create_or_update(self.resource_group_name, self.container_service_name, parameters))

    def delete_container_service(self):
        self.logfile.info('delete container service ...')
        client = ContainerServiceClient(self.credentials, self.subscription_id)
        #delete container service
        return client.container_services.delete(self.resource_group_name, self.container_service_name)

    def get_credentials(self):
        """Create the Resource Manager Client with an Application (service principal) token provider"""
        client = ContainerRegistryManagementClient(self.credentials, self.subscription_id)
        return self.create_credentials_json(client.registries.list_credentials(self.resource_group_name, self.registry_name))

    def create_credentials_json(self, group):
        credentials_result = {}
        credentials_result["username"] = group.username
        credentials_result["password"] = group.passwords[0].value
        return credentials_result

    def create_resource_group_result_json(self, group):
        resource_group_result = {}
        resource_group_result["resource_group_name"] = group.name
        resource_group_result["resource_group_id"] = group.id
        resource_group_result["resource_group_location"] = group.location
        resource_group_result["resource_group_tags"] = group.tags
        resource_group_result["resource_group_provisioning_state"] = group.properties.provisioning_state
        self.logfile.info('resource_group_result is: ' + str(resource_group_result))
        return resource_group_result

    def create_container_registry_result_json(self, group):
        container_result = {}
        container_result["container_name"] = group.result().name
        container_result["container_id"] = group.result().id
        container_result["container_location"] = group.result().location
        container_result["container_adminUserEnabled"] = group.result().admin_user_enabled
        container_result["container_provisioningState"] = group.result().provisioning_state.succeeded.value
        container_result["container_type"] = group.result().type
        self.logfile.info('container_registry_result is: ' + str(container_result))
        return container_result

    def create_container_service_result_json(self, group):
        service_result = {}
        service_result["service_name"] = group.result().name
        service_result["service_id"] = group.result().id
        service_result["service_master_name"] = group.result().master_profile.fqdn
        service_result["service_location"] = group.result().location
        service_result["service_type"] = group.result().type
        service_result["service_provisioningState"] = group.result().provisioning_state
        self.logfile.info('container_service_result is: ' + str(service_result))
        return service_result

    def create_public_ip_address_json(self, group):
        public_ip_result = {}
        public_ip_result["ip_address"] = group.result().ip_address
        self.logfile.info('public_ip_result is: ' + str(public_ip_result))
        return public_ip_result

def main():
    module = AnsibleModule(argument_spec=dict(
        location=dict(default='westeurope', type='str'),
        resource_group_action=dict(default='create', type='str'),
        resource_group_name=dict(type='str'),
        registry_name=dict(type='str'),
        sku=dict(default='Basic', type='str'),
        admin_user_enabled=dict(default=True,  type='bool'),
        container_service_name=dict(type='str'),
        cluster_name=dict(type='str'),
        master_dns_prefix=dict(type='str'),
        master_type=dict(type='str'),
        master_count=dict(default=1,  type='int'),
        sshpublickey=dict(type='str'),
        linux_user=dict(type='str'),
        agent_name=dict(type='str'),
        agent_dns_prefix=dict(type='str'),
        agent_type=dict(type='str'),
        agent_count=dict(default=3, type='int'),
        agent_os_type=dict(type='str'),
        storage_accounts_name=dict(type='str'),
        storage_accounts_sku=dict(type='str'),
        storage_accounts_kind=dict(type='str'),
        public_ip_address_name=dict(type='str'),
        domain_name_label=dict(type='str'),
        subscription_id=dict(type='str'),
        client_id=dict(type='str'),
        client_secret=dict(type='str'),
        tenant=dict(type='str')
    ))
    azureObj = AzureUtils(module)
    if azureObj.resource_group_action == "create":
        access_key = None
        create_resource_result = azureObj.create_resource_group()
        create_storage_accounts_result = azureObj.create_storage_accounts()
        access_key = azureObj.get_keys().keys[0].value
        create_registry_result = azureObj.create_container_registry(access_key)
        create_service_result = azureObj.create_container_service()
        deploy_k8s_result = {}
        deploy_k8s_result.update(create_resource_result)
        deploy_k8s_result.update(create_registry_result)
        deploy_k8s_result.update(create_service_result)
    elif azureObj.resource_group_action == "delete":
        azureObj.delete_container_service()
        azureObj.delete_container_registry()
        delete_resource_result = azureObj.delete_resource_group()
        deploy_k8s_result = ""
    elif azureObj.resource_group_action == "get_credentials":
        deploy_k8s_result = azureObj.get_credentials()
    elif azureObj.resource_group_action == "create_public_ip":
        deploy_k8s_result = azureObj.create_public_ip_address()
    else:
        module.fail_json(msg="Unsupported request type")
    result = {}
    result['changed'] = True
    result['response'] = deploy_k8s_result
    module.exit_json(**result)

if __name__ == "__main__":
    main()

