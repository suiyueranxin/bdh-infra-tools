#!/usr/bin/env python

import argparse
import datetime
import fnmatch
import json
import os
import subprocess


def call_kubectl(parms, output, print_err=True):
    command = ["kubectl"] + parms
    try:
        with open(output, 'wb') as output_file:
            subprocess.check_call(command, stderr=subprocess.STDOUT, stdout=output_file)
    except subprocess.CalledProcessError:
        if print_err:
            print("Error when calling " + " ".join(str(x) for x in command))
        # remove the files that are usually empty or only contain errors
        # from kubectl that are not relevant for bug reports
        os.remove(output)


def copy_pods_traces(namespace, dest_path, engine_name, skip_previous):
    res = subprocess.check_output(["kubectl", "get", "pods", "-o",
                                   "json", "-n", namespace])
    pod_data = json.loads(res)
    for pod in pod_data['items']:
        pod_name = pod['metadata']['name']
        if not fnmatch.fnmatch(pod_name, engine_name):
            print("Skipped non-selected pod: " + pod_name)
        else:
            print("Getting Logs for pod: " + pod_name)
            command_get_conts = ["kubectl", "get", "pods", pod_name, "-o", "jsonpath={.spec.containers[*].name}",
                                 "-n", namespace]
            conts = subprocess.check_output(command_get_conts, stderr=subprocess.STDOUT)
            for container in conts.split():
                timestamp = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d_%H-%M-%S.%f")
                args = ["logs", "-n", namespace, pod_name, "-c", container]
                if not skip_previous:
                    basename = "log_{}_{}_prev_{}.log"
                    call_kubectl(args + ["-p"],
                                 os.path.join(dest_path, basename.format(pod_name, container, timestamp)),
                                 False)
                basename = "log_{}_{}_{}.log"
                call_kubectl(args, os.path.join(dest_path, basename.format(pod_name, container, timestamp)))


def main():
    parser = argparse.ArgumentParser(
        description='Get the traces from the Kubernetes pods.'
    )

    parser.add_argument('--namespace', metavar='STRING', default='vora',
                        help='namespace of the pods (default: %(default)s)')
    parser.add_argument('--previous', action='store_true',
                        help=argparse.SUPPRESS)  # left for backwards compatibility
    parser.add_argument('--skip-previous', action='store_true',
                        help='do not include previous pod logs')
    parser.add_argument('--engine-name', metavar='PATTERN', default='*',
                        help='A name of the engine running inside pods '
                        '(default: %(default)s), example: *relational*')
    parser.add_argument('dest_path', help='path where to copy the traces')
    args = parser.parse_args()

    if not os.path.exists(args.dest_path):
        os.mkdir(args.dest_path)

    copy_pods_traces(args.namespace, args.dest_path, args.engine_name,
                     args.skip_previous)


if __name__ == "__main__":
    main()
