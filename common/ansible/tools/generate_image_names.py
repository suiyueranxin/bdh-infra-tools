#!/usr/bin/env python

from sys import argv, stdin, stderr
import re
import os

def get_image_list():
    list_of_images = []
    matcher = re.compile(r"(?P<host>[^/]*)/(?P<repo>[^:]*):(?P<tag>.*)")

    for url in sorted(set(stdin)):
        match = matcher.match(url.strip())
        if not match:
            print >> stderr, "WARNING: cannot match " + url
            continue

        list_of_images.append(
            (match.group('host'), match.group('repo'), match.group('tag')))

    return list_of_images

def generate_image_name_on_prem():
    provision_platform = os.getenv('PROVISION_PLATFORM', None)
    if not provision_platform:
        print >> stderr, "Can't find PROVISION_PLATFORM!"
        exit(1)

    target_hosts = []
    if provision_platform == "GKE":
        base_url = 'eu.gcr.io/sap-p-and-i-big-data-vora/'
        if 'GCP_DOCKER_REGISTRY_SUFFIX' in os.environ:
            target_hosts.append(base_url + os.environ['GCP_DOCKER_REGISTRY_SUFFIX'])
        else:
            cluster_name = os.getenv('K8S_CLUSTER_NAME', '')
            if not cluster_name:
                print >> stderr, "Can't find K8S_CLUSTER_NAME!"
                exit(1)
            target_hosts.append(base_url + cluster_name)
        if 'GCP_VFLOW_DOCKER_REGISTRY_SUFFIX' in os.environ:
            target_hosts.append(base_url + os.environ['GCP_VFLOW_DOCKER_REGISTRY_SUFFIX'])
    elif provision_platform == "AWS-EKS":
        base_url = '990498310577.dkr.ecr.eu-west-1.amazonaws.com'
        if 'EKS_DOCKER_REGISTRY_SUFFIX' in os.environ:
            target_hosts.append(base_url + '/' + os.environ['EKS_DOCKER_REGISTRY_SUFFIX'])
        else:
            target_hosts.append(base_url)
        if 'EKS_VFLOW_DOCKER_REGISTRY_SUFFIX' in os.environ:
            target_hosts.append(base_url + '/' + os.environ['EKS_VFLOW_DOCKER_REGISTRY_SUFFIX'])
    elif provision_platform == "AZURE-AKS":
        target_hosts.append('infrabase.azurecr.io')

    if len(target_hosts) == 0:
        print >> stderr, "Can't generate target registry host by provision_platform!"
        exit(1)

    default_repo = 'public.int.repositories.cloud.sap'

    image_list = get_image_list()

    for host, repo, tag in image_list: # pylint: disable=unused-variable
        image_name = repo + ':' + tag
        with open("/infrabox/output/image_name_list", "a+") as f:
            f.write(image_name + "\n")
        pull_url = default_repo + '/' + repo + ':' + tag
        for target_host in target_hosts:
            push_url = target_host + '/' + repo + ':' + tag
            with open("/tmp/pull_push_list", "a+") as f:
                f.write(pull_url + ";" + push_url + "\n")

def generate_image_name_on_cloud():
    target_host = '726853116465.dkr.ecr.eu-central-1.amazonaws.com/dev'
    default_repo = '73554900100900002861.dockersrv.repositories.sap.ondemand.com'
    xmake_repos = {
        'sap': 'public.int.repositories.cloud.sap',
        'foss': 'public.int.repositories.cloud.sap'
    }
    list_of_images = get_image_list()

    for host, repo, tag in list_of_images:
        if repo == 'com.sap.datahub.linuxx86_64/installer':
            host = 'di-dev-cicd-v2.int.repositories.cloud.sap/infrabox/hanalite-releasepack'

        if host == default_repo:
            if repo.startswith('com.sap'):
                host = xmake_repos['sap']
            else:
                host = xmake_repos['foss']

        pull_url = host + '/' + repo + ':' + tag
        push_url = target_host + '/' + repo + ':' + tag
        image_name = repo + ':' + tag
        with open("/project/pull_push_list", "a+") as f:
            f.write(pull_url + ";" + push_url + "\n")
        with open("/infrabox/output/image_name_list", "a+") as f:
            f.write(image_name + "\n")

if __name__ == "__main__":
    mirror_type = argv[1]
    if mirror_type == "on_prem":
        generate_image_name_on_prem()
    else:
        generate_image_name_on_cloud()
