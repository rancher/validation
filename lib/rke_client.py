from invoke import run
import os
import jinja2
import tempfile


DEFAULT_CONFIG_NAME = 'cluster.yml'
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../resources/rke_templates')
DEBUG = os.environ.get('DEBUG', 'false')


class RKEClient(object):
    """
    Wrapper to interact with the RKE cli
    """
    def __init__(self, master_ssh_key_path):
        self.master_ssh_key_path = master_ssh_key_path
        self._working_dir = tempfile.mkdtemp()
        self._hide = False if DEBUG.lower() == 'true' else True

    def _run(self, command):
        return run(
            'cd {0} && {1}'.format(self._working_dir, command),
            warn=True, hide=self._hide)

    def up(self, config_yml, config=None):
        yml_name = config if config else DEFAULT_CONFIG_NAME
        self._save_cluster_yml(yml_name, config_yml)
        cli_args = '' if config is None else ' --config {0}'.format(config)
        result = self._run("rke up {0}".format(cli_args))
        return result

    def remove(self, config=None, force=False):
        result = run("rke remove")
        return result

    def build_rke_template(self, template, nodes, **kwargs):
        render_dict = {'master_ssh_key_path': self.master_ssh_key_path}
        render_dict.update(kwargs)  # will up master_key if passed in
        node_index = 0
        for node in nodes:
            node_dict = {
                'ssh_user_{}'.format(node_index): node.ssh_user,
                'ip_address_{}'.format(node_index): node.public_ip_address,
                'dns_hostname_{}'.format(node_index): node.host_name,
                'ssh_key_path_{}'.format(node_index): node.ssh_key_path,
                'ssh_key_{}'.format(node_index): node.ssh_key,
                'internal_address_{}'.format(node_index):
                    node.private_ip_address,
            }
            render_dict.update(node_dict)
            node_index += 1
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATE_PATH)
        ).get_template(template).render(render_dict)

    def _save_cluster_yml(self, yml_name, yml_contents):
        file_path = "{}/{}".format(self._working_dir, yml_name)
        with open(file_path, 'w') as f:
            f.write(yml_contents)

    def get_kube_config_for_config(self, yml_name=DEFAULT_CONFIG_NAME):
        file_path = "{}/.kube_config_{}".format(self._working_dir, yml_name)
        with open(file_path, 'r') as f:
            kube_config = f.read()
        return kube_config

    def kube_config_path(self, yml_name=DEFAULT_CONFIG_NAME):
        return os.path.abspath(
            "{}/.kube_config_{}".format(self._working_dir, yml_name))
