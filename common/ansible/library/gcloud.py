#!/usr/bin/python

import copy
import yaml

from google.api_core import retry
from google.cloud import container_v1
from ansible.module_utils.basic import AnsibleModule


class gcloudContainer:
    def __init__(self, project_id, zone):
        self.gclient = container_v1.ClusterManagerClient()
        self.gclinetRetry = retry.Retry()
        self.gcloud_project_id = project_id
        self.gcloud_zone = zone
        self.clusterInfo = {}
        self.clusterNodeConfig = {}
        self.addonConfig = {}
        self.timeout = 300
        self.description = 'Automatically deployed by SAP DH Infra team ...'
        self.clusterNodeOauthScopes = ['https://www.googleapis.com/auth/compute',
                                       'https://www.googleapis.com/auth/devstorage.read_write',
                                       'https://www.googleapis.com/auth/logging.write',
                                       'https://www.googleapis.com/auth/monitoring',
                                       'https://www.googleapis.com/auth/servicecontrol',
                                       'https://www.googleapis.com/auth/service.management.readonly',
                                       'https://www.googleapis.com/auth/trace.append']
        self.clusterAdmCfgTempDict = {'kind': 'Config',
                                      'preferences': {}, 'current-context': '',
                                      'contexts': [{'name': '', 'context': {'cluster': '', 'user': ''}}],
                                      'clusters': [{'cluster': {'certificate-authority-data': '', 'server': ''},
                                      'name': ''}],
                                      'apiVersion': 'v1', 'users': [{'name': '',
                                      'user': {'as-user-extra': {},'username': '', 'password': ''}}]}

    def buildClusterInfo(self, cluster_name, cluster_version, cluster_nodeCount, cluster_machine_type, cluster_node_disk_size, cluster_image_type, cluster_vpc, cluster_subnetwork):
        self.clusterInfo['initial_node_count'] = int(cluster_nodeCount)
        self.clusterInfo['description'] = self.description
        self.clusterInfo['name'] = cluster_name
        self.clusterInfo['zone'] = self.gcloud_zone
        self.clusterInfo['initial_cluster_version'] = cluster_version
        self.clusterInfo['network'] = cluster_vpc
        self.clusterInfo['subnetwork'] = cluster_subnetwork
#        self.clusterInfo['services_ipv4_cidr'] = '172.1.0.0/16'
        self.clusterInfo['network_policy'] = {"provider": "CALICO"}
#        self.clusterInfo['autoscaling'] = {}
        self.clusterInfo['ip_allocation_policy'] = {}
        self.clusterInfo['master_authorized_networks_config'] = {}
        self.clusterNodeConfig['machine_type'] = cluster_machine_type
        self.clusterNodeConfig['disk_size_gb'] = int(cluster_node_disk_size)
        self.clusterNodeConfig['image_type'] = cluster_image_type
        self.clusterNodeConfig['oauth_scopes'] = self.clusterNodeOauthScopes
        self.clusterInfo['node_config'] = self.clusterNodeConfig
        self.addonConfig['http_load_balancing'] = {}
        self.addonConfig['kubernetes_dashboard'] = {}
        self.addonConfig['network_policy_config'] = {'disabled': True}
        self.clusterInfo['addons_config'] = self.addonConfig

    def deployK8s(self):
        resp = self.gclient.create_cluster(self.gcloud_project_id, self.gcloud_zone, self.clusterInfo, self.gclinetRetry, self.timeout)
        return self.buildResponse(resp, 'deploy')

    def createK8sAdmCfg(self, cluster_name, cfglocal_path):
        ret = {'name': 'create k8s admin config file', 'status': '', 'path': ''}
        resp = self.getK8sCluster(cluster_name)
        admcfgDict = self.buildAdmCfg(resp)
        admcfgFile = cfglocal_path
        with open(admcfgFile, 'w') as cfgfile:
            try:
                yaml.safe_dump(admcfgDict, cfgfile, default_flow_style=False)
                ret['status'] = 'succeed'
                ret['path'] = admcfgFile
            except yaml.YAMLError as exc:
                print exc
                ret['status'] = 'failed'
        return ret

    def getK8sCluster(self, cluster_name):
        resp = self.gclient.get_cluster(self.gcloud_project_id, self.gcloud_zone, cluster_name, self.gclinetRetry, self.timeout)
        return resp

    def getK8scState(self, cluster_name):
        resp = self.gclient.get_cluster(self.gcloud_project_id, self.gcloud_zone, cluster_name, self.gclinetRetry, self.timeout)
        return self.buildResponse(resp, 'state')

    def deleteK8s(self, cluster_name):
        resp = self.gclient.delete_cluster(self.gcloud_project_id, self.gcloud_zone, cluster_name, self.gclinetRetry, self.timeout)
        return self.buildResponse(resp, 'delete')

    def buildResponse(self, container_v1_types_Operation, opType):
        ret = {}
        if opType in ['deploy', 'delete']:
            ret['name'] = container_v1_types_Operation.name
            ret['operation_type'] = container_v1_types_Operation.operation_type
            ret['status'] = container_v1_types_Operation.status
            ret['self_link'] = container_v1_types_Operation.self_link
            ret['target_link'] = container_v1_types_Operation.target_link
            ret['start_time'] = container_v1_types_Operation.start_time
            ret['zone'] = container_v1_types_Operation.zone
        elif opType == 'state':
            ret['name'] = container_v1_types_Operation.name
            ret['status'] = container_v1_types_Operation.status
            ret['zone'] = container_v1_types_Operation.zone
            ret['endpoint'] = container_v1_types_Operation.endpoint
            ret['initial_cluster_version'] = container_v1_types_Operation.initial_cluster_version
            ret['current_master_version'] = container_v1_types_Operation.current_master_version
            ret['current_node_version'] = container_v1_types_Operation.current_node_version
            ret['create_time'] = container_v1_types_Operation.create_time
            ret['current_node_count'] = container_v1_types_Operation.current_master_version
        return ret

    def buildAdmCfg(self, container_v1_types_Cluster):
        admCfg = copy.deepcopy(self.clusterAdmCfgTempDict)
        context = 'gke_' + self.gcloud_project_id + '_' + container_v1_types_Cluster.zone + '_' + container_v1_types_Cluster.name
        admCfg['current-context'] = context
        admCfg['contexts'][0]['name'] = context
        admCfg['contexts'][0]['context']['cluster'] = context
        admCfg['contexts'][0]['context']['user'] = context
        admCfg['clusters'][0]['cluster']['certificate-authority-data'] = container_v1_types_Cluster.master_auth.cluster_ca_certificate
        admCfg['clusters'][0]['cluster']['server'] = 'https://' + container_v1_types_Cluster.endpoint
        admCfg['clusters'][0]['name'] = context
        admCfg['users'][0]['name'] = context
        #admCfg['users'][0]['user']['client-certificate-data'] = container_v1_types_Cluster.master_auth.client_certificate
        admCfg['users'][0]['user']['username'] = container_v1_types_Cluster.master_auth.username
        admCfg['users'][0]['user']['password'] = container_v1_types_Cluster.master_auth.password

        return admCfg


def main():
    module = AnsibleModule(argument_spec=dict(
        k8s_cluster_name=dict(required=True, type='str'),
        k8s_cluster_version=dict(required=False, type='str'),
        request_type=dict(required=True, choices=['create',
                                                  'delete',
                                                  'getconf',
                                                  'state'], type='str'),
        k8s_cluster_node_num=dict(required=False, type='int'),
        k8s_cluster_node_machine_type=dict(required=False, type='str'),
        k8s_cluster_node_image_type=dict(required=False, type='str'),
        k8s_cluster_node_disk_size=dict(required=False, type='str'),
        k8s_cluster_zone=dict(required=True, type='str'),
        k8s_cluster_vpc=dict(required=False, type='str'),
        k8s_cluster_subnetwork=dict(required=False, type='str'),
        k8s_cluster_project_id=dict(required=True, type='str'),
        k8s_cluster_admcfg_local_path=dict(required=False, type='str'),))

    gcloudClient = gcloudContainer(module.params['k8s_cluster_project_id'], module.params['k8s_cluster_zone'])

    try:
        if module.params['request_type'] == 'create':
            gcloudClient.buildClusterInfo(module.params['k8s_cluster_name'],
                                          module.params['k8s_cluster_version'],
                                          module.params['k8s_cluster_node_num'],
                                          module.params['k8s_cluster_node_machine_type'],
                                          module.params['k8s_cluster_node_disk_size'],
                                          module.params['k8s_cluster_node_image_type'],
                                          module.params['k8s_cluster_vpc'],
                                          module.params['k8s_cluster_subnetwork'])
            response = gcloudClient.deployK8s()
        elif module.params['request_type'] == 'delete':
            response = gcloudClient.deleteK8s(module.params['k8s_cluster_name'])
        elif module.params['request_type'] == 'getconf':
            response = gcloudClient.createK8sAdmCfg(module.params['k8s_cluster_name'], module.params['k8s_cluster_admcfg_local_path'])
        elif module.params['request_type'] == 'state':
            response = gcloudClient.getK8scState(module.params['k8s_cluster_name'])
        else:
            module.fail_json(msg="Unsupported request type:" + module.params['request_type'])
    # pylint: disable=W0703
    except Exception as e:
        module.fail_json(msg="exception found when execute this module", debug_msg=str(e))

    result = {}
    if response['status'] != 'failed':
        result['changed'] = True
    else:
        result['changed'] = False
    result['response'] = response

    module.exit_json(**result)


if __name__ == '__main__':
    main()
