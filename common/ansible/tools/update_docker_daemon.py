#!/usr/bin/env python
import os
import os.path
import json
import sys
import re

file_path = sys.argv[1]
to_ops = False
daemon_file = '/etc/docker/daemon.json'
if len(sys.argv) > 2 and sys.argv[2].lower() == "true":
    # if enabled, program will print "--insecure-registry=xxx --insecure-registry=yyy"
    # instead of updating daemon file
    # this case is used for updating /etc/default/docker file
    to_ops = True

docker_registry = []

with open(file_path, 'r') as f:
    lines = f.read()
    matches = re.finditer(r'IMAGE_SOURCE_CUSTOM=([^/]+)/', lines, re.MULTILINE)
    for match in matches:
        for group in match.groups():
            if not to_ops:
                print "source: " + group
            if group not in docker_registry:
                docker_registry.append(group)

if len(docker_registry) > 0:
    if to_ops:
        print ' '.join(["--insecure-registry={}".format(x) for x in docker_registry])
    else:
        daemon_json = {}
        if os.path.isfile(daemon_file):
            daemon_json = json.load(open(daemon_file, 'r'))
        if 'insecure-registries' not in daemon_json:
            daemon_json['insecure-registries'] = []
        for source in docker_registry:
            if source not in daemon_json['insecure-registries']:
                daemon_json['insecure-registries'].append(source)

        with open(daemon_file, 'w+') as outfile:
            json.dump(daemon_json, outfile)
