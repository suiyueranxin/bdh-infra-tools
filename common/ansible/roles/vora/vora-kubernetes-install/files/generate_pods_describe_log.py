import json
import os
import sys
import subprocess

def generate_pods_describe(namespace, dest_path):
    pods_status = subprocess.check_output(["kubectl", "get", "pods", "-n", namespace])
    if isinstance(pods_status, bytes):
        pods_status = pods_status.decode("utf-8")
    if pods_status.find("No resources found") >= 0:
        print("No resources found")
        return
    with open(os.path.join(dest_path, "index"), "w") as f:
        f.write(pods_status)

    res = subprocess.check_output(["kubectl", "get", "pods", "-o",
                                   "json", "-n", namespace])
    if isinstance(res, bytes):
        res = res.decode("utf-8")                               
    pod_data = json.loads(res)
    for pod in pod_data['items']:
        pod_name = pod['metadata']['name']
        print("Getting Describe for pod: " + pod_name)
        command_get_conts = ["kubectl", "describe" , "pod", pod_name, "-n", namespace]
        conts = subprocess.check_output(command_get_conts, stderr=subprocess.STDOUT)
        if isinstance(conts, bytes):
            conts = conts.decode("utf-8")  
        with open(os.path.join(dest_path, pod_name), "w") as f:
            f.write(conts)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Lost of parameters")
        exit(1)
    namespace = sys.argv[1]
    folder = sys.argv[2]
    namespace_folder = os.path.join(folder, 'namespace')
    if not os.path.exists(namespace_folder):
        os.makedirs(namespace_folder)
    generate_pods_describe(namespace, namespace_folder)

    system_namespace = 'kube-system'
    system_folder = os.path.join(folder, 'system')
    if not os.path.exists(system_folder):
        os.makedirs(system_folder)
    generate_pods_describe(system_namespace, system_folder)
