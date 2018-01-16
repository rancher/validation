from invoke import run
import os
import jinja2
import tempfile

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../resources/rke_templates')


class RKEClient(object):
    """
    Wrapper to interact with the RKE cli
    """
    def __init__(self):
        self._working_dir = tempfile.mkdtemp()

    def _run(self, command):
        return run(
            'cd {0} && {1}'.format(self._working_dir, command), warn=True)

    def up(self, config=None):
        cli_args = '' if config is None else ' --config {0}'.format(config)
        result = self._run("rke up {0}".format(cli_args))
        return result

    def remove(self, config=None, force=False):
        result = run("rke remove")
        return result

    def build_rke_template(self, template, nodes, **kwargs):
        render_dict = {}
        render_dict.update(kwargs)
        node_index = 0
        for node in nodes:
            node_dict = {
                'ssh_user_{}'.format(node_index): node.ssh_user,
                'host_name_ip_{}'.format(node_index): node.public_ip_address
            }
            render_dict.update(node_dict)
            node_index += 1
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATE_PATH)
        ).get_template(template).render(render_dict)

    def save_cluster_yml(self, yml_name, yml_contents):
        file_path = "{}/{}".format(self._working_dir, yml_name)
        with open(file_path, 'w') as f:
            f.write(yml_contents)

    def get_kube_config_for_config(self, yml_name='cluster.yml'):
        file_path = "{}/.kube_config_{}".format(self._working_dir, yml_name)
        with open(file_path, 'r') as f:
            kube_config = f.read()
        return kube_config