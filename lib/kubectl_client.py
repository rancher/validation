import os
from invoke import run
import json
import time


DEBUG = os.environ.get('DEBUG', 'false')


class KubectlClient(object):

    def __init__(self):
        self._kube_config_path = None
        self._hide = False if DEBUG.lower() == 'true' else True

    @property
    def kube_config_path(self):
        return self._kube_config_path

    @kube_config_path.setter
    def kube_config_path(self, value):
        self._kube_config_path = value

    @staticmethod
    def _load_json(output):
        if output == '':
            return None
        return json.loads(output)

    def execute_kubectl_cmd(self, cmd, json_out=True):
        command = 'kubectl --kubeconfig {0} {1}'.format(
            self.kube_config_path, cmd)
        if json_out:
            command += ' -o json'
        print "Running kubectl command: {}".format(command)
        start_time = time.time()
        result = run(command, warn=True, hide=self._hide)
        end_time = time.time()
        print 'Run time for command {0}: {1} seconds'.format(
            command, end_time - start_time)
        return result

    def exec_cmd(self, pod, cmd, namespace):
        result = self.execute_kubectl_cmd(
            'exec {0} --namespace={1} -- {2}'.format(pod, namespace, cmd),
            json_out=False)
        return result

    def logs(self, pod, namespace=None, container=None):
        command = 'logs {0}'.format(pod)
        # TODO if logs output is too large:
        #  --limit-bytes=10000: Maximum bytes of logs to return
        if namespace:
            command += ' --namespace={0}'.format(namespace)
        if container:
            command += ' --container={0}'.format(container)
        result = self.execute_kubectl_cmd(command, json_out=False)
        return result

    def create_ns(self, namespace):
        self.execute_kubectl_cmd("create namespace " + namespace)
        # Verify namespace is created
        result = self.execute_kubectl_cmd("get namespace " + namespace)
        secret = self._load_json(result.stdout)
        assert secret["metadata"]["name"] == namespace
        assert secret["status"]["phase"] == "Active"
        return secret

    def create_resourse_from_yml(self, file_yml, namespace=None):
        cmd = "create -f {0}".format(file_yml)
        if namespace:
            cmd += ' --namespace={0}'.format(namespace)
        return self.execute_kubectl_cmd(cmd)

    def delete_resourse_from_yml(self, file_yml, namespace=None):
        cmd = "delete -f {0}".format(file_yml)
        if namespace:
            cmd += ' --namespace={0}'.format(namespace)
        return self.execute_kubectl_cmd(cmd, json_out=False)

    def delete_resourse(self, resource, resource_name, namespace=None):
        cmd = "delete {0} {1}".format(resource, resource_name)
        if namespace:
            cmd += ' --namespace={0}'.format(namespace)
        return self.execute_kubectl_cmd(cmd, json_out=False)

    def get_all_ns(self):
        result = self.execute_kubectl_cmd("get namespace")
        ns = self._load_json(result.stdout)
        return ns['items']

    def get_nodes(self):
        result = self.execute_kubectl_cmd("get nodes")
        nodes = self._load_json(result.stdout)
        return nodes

    def get_resource(
            self, resource, resource_name=None, namespace=None, selector=None):
        cmd = "get {0}".format(resource)
        if resource_name:
            cmd += ' {0}'.format(resource_name)
        if namespace:
            cmd += ' --namespace={0}'.format(namespace)
        if selector:
            cmd += ' --selector={0}'.format(selector)
        result = self.execute_kubectl_cmd(cmd)
        return self._load_json(result.stdout)

    def wait_for_pods(self, selector, namespace=None, number_of_pods=1,
                      state='Running'):
        start_time = int(time.time())
        while True:
            pods = self.get_resource(
                'pod', selector=selector, namespace=namespace)
            if len(pods.get('items', 0)) == number_of_pods:
                print "Number of pods {0}".format(len(pods['items']))
                for pod in pods['items']:
                    if pod['status']['phase'] != state:
                        break
                else:
                    time.sleep(5)
                    return pods
            if int(time.time()) - start_time > 300:
                raise Exception(
                    'Timeout Exception: pods did not start\n'
                    'Expect number of pods {0} vs number of pods found {1}\n'
                    .format(number_of_pods, len(pods['items'])))
            time.sleep(5)
