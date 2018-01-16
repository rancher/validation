import abc
import os
from invoke import run


class CloudProviderBase(object):
    __metaclass__ = abc.ABCMeta

    OS_VERSION = os.getenv("OS_VERSION", 'ubuntu-16.04')
    DOCKER_VERSION = os.getenv("DOCKER_VERSION", '1.12.6')

    @abc.abstractmethod
    def create_node(self, node_name, wait_for_ready=False):
        raise NotImplementedError

    # @abc.abstractmethod
    # def get_node(self):
    #     raise NotImplementedError

    @abc.abstractmethod
    def stop_node(self, node, wait_for_stop=False):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_node(self, wait_for_delete=False):
        raise NotImplementedError

    @abc.abstractmethod
    def import_ssh_key(self, ssh_key_name, public_ssh_key):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_ssh_key(self, ssh_key_name):
        raise NotImplementedError

    def save_master_key(self, ssh_key_name, ssh_key):
        if not os.path.isfile('.ssh/{}'.format(ssh_key_name)):
            with open('.ssh/{}'.format(ssh_key_name), 'w') as f:
                f.write(ssh_key)
            run("chmod 0600 .ssh/{0}".format(ssh_key_name))
            run("cat .ssh/{}".format(ssh_key_name))

    def generate_ssh_key(self, ssh_key_name):
        try:
            if not os.path.isfile('.ssh/{}'.format(ssh_key_name)):
                run('mkdir -p .ssh && rm -rf .ssh/{}'.format(ssh_key_name))
                run("ssh-keygen -N '' -C '{0}' -f .ssh/{0}".format(
                    ssh_key_name))
                run("chmod 0600 .ssh/{0}".format(ssh_key_name))

            public_ssh_key = self.get_public_ssh_key(ssh_key_name)
        except Exception as e:
            raise Exception("Failed to generate ssh key: {0}".format(e))
        return public_ssh_key

    def get_public_ssh_key(self, ssh_key_name):
        try:
            with open('.ssh/{}.pub'.format(ssh_key_name), 'r') as f:
                ssh_key = f.read()
        except Exception:
            ssh_key = None
        return ssh_key

    def get_ssh_key_path(self, ssh_key_name):
        return os.path.abspath('.ssh/{}'.format(ssh_key_name))
