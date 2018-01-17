import os
from invoke import run
import json
import jinja2


k8s_base_lb_port = os.environ.get("BASE_LB_PORT", "88")
k8s_base_external_port = os.environ.get("BASE_EXTERNAL_PORT", "300")
k8s_base_node_port = os.environ.get("BASE_NODE_PORT", "310")
k8s_base_ingress_port = os.environ.get("BASE_INGRESS_PORT", "8")
k8s_base_lb_node_port = os.environ.get("BASE_LB_NODE_PORT", "320")

K8_SUBDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         '../resources/k8s_templates')

DEBUG = os.environ.get('DEBUG', 'false')


class KubectlClient(object):

    def __init__(self):
        self._kube_config_path = None
        self._hide = False if DEBUG.tolower() == 'true' else True

    @property
    def kube_config_path(self):
        return self._kube_config_path

    @kube_config_path.setter
    def kube_config_path(self, value):
        self._kube_config_path = value

    def execute_kubectl_cmd(self, cmd):
        return run('kubectl --kubeconfig {} {} -o json'.format(
            self.kube_config_path, cmd), warn=True, hide=self._hide)

    def create_ns(self, namespace):
        self.execute_kubectl_cmd("create namespace " + namespace)
        # Verify namespace is created
        result = self.execute_kubectl_cmd("get namespace " + namespace)
        secret = json.loads(result.stdout)
        assert secret["metadata"]["name"] == namespace
        assert secret["status"]["phase"] == "Active"

    def get_all_ns(self):
        result = self.execute_kubectl_cmd("get namespace")
        ns = json.loads(result.stdout)
        return ns['items']

    def get_all_nodes(self):
        result = self.execute_kubectl_cmd("get nodes")
        nodes = json.loads(result.stdout)
        return nodes

    def create_validation_stack(self, input_config):
        namespace = input_config["namespace"]
        self.create_ns(namespace)

        # Create pre upgrade resources
        nodes = self.get_all_nodes()
        node1 = nodes['items'][0]['status']['addresses'][0]['address']

        # Render the testing yaml
        input_config["external_node"] = node1
        input_config["k8s_base_lb_port"] = k8s_base_lb_port
        input_config["k8s_base_external_port"] = k8s_base_external_port + "0"
        input_config["k8s_base_node_port"] = k8s_base_node_port + "0"
        input_config["k8s_base_lb_node_port"] = k8s_base_lb_node_port + "0"
        input_config["k8s_base_ingress_port"] = k8s_base_ingress_port
        if len(input_config["port_ext"]) > 1:
            input_config["k8s_base_external_port"] = k8s_base_external_port
            input_config["k8s_base_node_port"] = k8s_base_node_port
            input_config["k8s_base_lb_node_port"] = k8s_base_lb_node_port
        fname = os.path.join(K8_SUBDIR, "validation.yml.j2")
        rendered_tmpl = self._jinja2_render(fname, input_config)

        with open(os.path.join("validation.yml"), "w") as fout:
            fout.write(rendered_tmpl)

        return self.execute_kubectl_cmd(
            "create --namespace=" + namespace + " -f validation.yml")

    def _jinja2_render(self, tpl_path, context):
        path, filename = os.path.split(tpl_path)
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(path)
        ).get_template(filename).render(context)
