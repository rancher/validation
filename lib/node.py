import paramiko
import json


class Node(object):
    def __init__(
        self, provider_node_id=None, host_name=None, node_name=None,
        public_ip_address=None, private_ip_address=None, state=None,
        labels=None, host_name_override=None, ssh_key=None,
            ssh_key_name=None, ssh_key_path=None, ssh_user=None):

        self.provider_node_id = provider_node_id
        self.node_name = node_name
        self.host_name = host_name
        self.host_name_override = host_name_override
        self.public_ip_address = public_ip_address
        self.private_ip_address = private_ip_address
        self.ssh_user = ssh_user
        self.ssh_key = ssh_key
        self.ssh_key_name = ssh_key_name
        self.ssh_key_path = ssh_key_path
        self.roles = None
        self.labels = labels or {}
        self.state = state
        self._ssh_client = paramiko.SSHClient()
        self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_port = '22'

    def execute_command(self, command):
        result = None
        try:
            self._ssh_client.connect(
                self.public_ip_address, username=self.ssh_user,
                key_filename=self.ssh_key_path, port=self.ssh_port)
            result = self._ssh_client.exec_command(command)
            if result and len(result) == 3 and result[1].readable():
                result = [result[1].read(), result[2].read()]
        finally:
            self._ssh_client.close()
        return result

    def docker_ps(self, all=False):
        result = self.execute_command(
            'docker ps --format "{{.Names}}\t{{.Image}}"')
        if result[1] != '':
            raise Exception(
                "Error:'docker ps' command received this stderr output: "
                "{0}".format(result[1]))
        parse_out = result[0].strip('\n').split('\n')
        ret_dict = {}
        if parse_out == '':
            return ret_dict
        for item in parse_out:
            item0, item1 = item.split('\t')
            ret_dict[item0] = item1
        return ret_dict

    def docker_inspect(self, container_name, output_format=None):
        if output_format:
            command = 'docker inspect --format \'{0}\' {1}'.format(
                output_format, container_name)
        else:
            command = 'docker inspect {0}'.format(container_name)
        result = self.execute_command(command)
        if result[1] != '':
            raise Exception(
                "Error:'docker inspect' command received this stderr output: "
                "{0}".format(result[1]))
        result = json.loads(result[0])
        return result

    def docker_exec(self, container_name, cmd):
        command = 'docker exec {0} {1}'.format(container_name, cmd)
        result = self.execute_command(command)
        if result[1] != '':
            raise Exception(
                "Error:'docker exec' command received this stderr output: "
                "{0}".format(result[1]))
        return result[0]


def test_nodes(number_nodes):
    """
    Used to debug/test test framework code
    """
    nodes = []
    for i in range(number_nodes):
        nodes.append(Node(
            ssh_user='ubuntu',
            public_ip_address='{0}.{0}.{0}.{0}'.format(i + 1),
            host_name='mydns.{0}'.format(i + 1),
            ssh_key_path='my/own/key',
            ssh_key='BEGIN\nsdasd\nEND',
            private_ip_address='10.{0}.{0}.{0}'.format(i + 1)
        ))
    return nodes
