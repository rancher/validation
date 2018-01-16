import boto3
import os
import time
from boto3.exceptions import Boto3Error

from cloud_provider import CloudProviderBase
from node import Node


AWS_REGION = 'us-east-2'
AWS_REGION_AZ = 'us-east-2a'
AWS_SECURITY_GROUPS = ['sg-3076bd59']
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_SSH_KEY_NAME = os.environ.get("AWS_SSH_KEY_NAME")

AWS_INSTANCE_TYPE = os.environ.get("AWS_INSTANCE_TYPE", 't2.micro')
PRIVATE_IMAGES = {
    "ubuntu-16.04-docker-1.12.6": {
        'image': 'ami-cf6c47aa', 'ssh_user': 'ubuntu'},
    "ubuntu-16.04-docker-1.13.1": {
        'image': 'ami-4c7c5729', 'ssh_user': 'ubuntu'},
    "ubuntu-16.04-docker-17.03": {
        'image': 'ami-a77259c2', 'ssh_user': 'ubuntu'},
    "ubuntu-16.04-docker-17.12": {
        'image': 'ami-f9644e9c', 'ssh_user': 'ubuntu'},
    "ubuntu-16.04-docker-latest": {
        'image': 'ami-f9644e9c', 'ssh_user': 'ubuntu'},
    "rhel-7.4-docker-1.12.6": {
        'image': 'ami-1f6c477a', 'ssh_user': 'ec2-user'}}


class AmazonWebServices(CloudProviderBase):

    def __init__(self):
        self._client = boto3.client(
            'ec2',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION)

        if AWS_SSH_KEY_NAME:
            self._master_ssh_key = self.get_ssh_key(AWS_SSH_KEY_NAME)

        # Used for cleanup
        self.created_node = []
        self.created_keys = []

    def _select_ami(self):
        image = PRIVATE_IMAGES[
            "{}-docker-{}".format(self.OS_VERSION, self.DOCKER_VERSION)]
        return image['image'], image['ssh_user']

    def create_node(self, node_name, key_name=None, wait_for_ready=False):
        image, ssh_user = self._select_ami()
        if key_name:
            ssh_key = self.get_ssh_key(key_name)
            ssh_key_path = self.get_ssh_key_path(key_name),
        else:
            key_name = AWS_SSH_KEY_NAME
            ssh_key = self._master_ssh_key
            ssh_key_path = self.get_ssh_key_path(key_name)

        instance = self._client.run_instances(
            ImageId=image,
            InstanceType=AWS_INSTANCE_TYPE,
            MinCount=1, MaxCount=1,
            TagSpecifications=[{'ResourceType': 'instance', 'Tags': [
                {'Key': 'Name', 'Value': node_name},
                {'Key': 'CICD', 'Value': 'rke'}]}],
            KeyName=key_name,
            NetworkInterfaces=[{
                'DeviceIndex': 0,
                'AssociatePublicIpAddress': True,
                'Groups': AWS_SECURITY_GROUPS}],
            Placement={'AvailabilityZone': AWS_REGION_AZ})

        node = Node(
            node_name=node_name,
            provider_node_id=instance['Instances'][0]['InstanceId'],
            state=instance['Instances'][0]['State']['Name'],
            ssh_user=ssh_user,
            ssh_key_name=key_name,
            ssh_key_path=ssh_key_path,
            ssh_key=ssh_key)

        # mark for clean up at the end
        self.created_node.append(node.provider_node_id)

        if wait_for_ready:
            node = self.wait_for_node_state(node)

        return node

    def create_multiple_nodes(self, number_of_nodes, node_name_prefix,
                              key_name=None, wait_for_ready=False):
        nodes = []
        for i in range(number_of_nodes):
            node_name = "{}_{}".format(node_name_prefix, i)
            nodes.append(self.create_node(node_name, key_name))

        if wait_for_ready:
            nodes = self.wait_for_nodes_state(nodes)
        return nodes

    def get_node(self, provider_id):
        node_filter = [{
            'Name': 'instance-id', 'Values': [provider_id]}]
        try:
            response = self._client.describe_instances(Filters=node_filter)
            nodes = response.get('Reservations', [])
            if len(nodes) == 0:
                return None  # no node found

            aws_node = nodes[0]['Instances'][0]
            node = Node(
                provider_node_id=provider_id,
                # node_name= aws_node tags?,
                host_name=aws_node.get('PublicDnsName'),
                public_ip_address=aws_node.get('PublicIpAddress'),
                private_ip_address=aws_node.get('PrivateIpAddress'),
                state=aws_node['State']['Name'])
            return node
        except Boto3Error as e:
            msg = "Failed while querying instance '{}' state!: {}".format(
                node.node_id, str(e))
            raise RuntimeError(msg)

    def update_node(self, node):
        node_filter = [{
            'Name': 'instance-id', 'Values': [node.provider_node_id]}]
        try:
            response = self._client.describe_instances(Filters=node_filter)
            nodes = response.get('Reservations', [])
            if len(nodes) == 0 or len(nodes[0]['Instances']) == 0:
                return node

            aws_node = nodes[0]['Instances'][0]
            node.state = aws_node['State']['Name']
            node.host_name = aws_node.get('PublicDnsName')
            node.public_ip_address = aws_node.get('PublicIpAddress')
            node.private_ip_address = aws_node.get('PrivateIpAddress')
            return node
        except Boto3Error as e:
            msg = "Failed while querying instance '{}' state!: {}".format(
                node.node_id, str(e))
            raise RuntimeError(msg)

    def stop_node(self, node, wait_for_stopped=False):
        self._client.stop_instances(
            InstanceIds=[node.provider_node_id])
        if wait_for_stopped:
            node = self.wait_for_node_state(node, 'stopped')
        return node

    def delete_node(self, node, wait_for_deleted=False):
        self._client.terminate_instances(
            InstanceIds=[node.provider_node_id])
        if wait_for_deleted:
            node = self.wait_for_node_state(node, 'terminated')
        return node

    def wait_for_node_state(self, node, state='running'):
        # 'running', 'stopped', 'terminated'
        timeout = 300
        start_time = time.time()
        while time.time() - start_time < timeout:
            node = self.update_node(node)
            if node.state == state:
                time.sleep(20)
                return node
            time.sleep(5)

    def wait_for_nodes_state(self, nodes, state='running'):
        # 'running', 'stopped', 'terminated'
        timeout = 300
        start_time = time.time()
        completed_nodes = []
        while time.time() - start_time < timeout:
            for node in nodes:
                if len(completed_nodes) == len(nodes):
                    return completed_nodes
                if node in completed_nodes:
                    continue
                node = self.update_node(node)
                if node.state == state:
                    completed_nodes.append(node)
                time.sleep(1)
            time.sleep(4)

    def import_ssh_key(self, ssh_key_name, public_ssh_key):
        self._client.delete_key_pair(KeyName=ssh_key_name)
        self._client.import_key_pair(
            KeyName=ssh_key_name,
            PublicKeyMaterial=public_ssh_key)
        # mark keys for cleanup
        self.created_keys.append(ssh_key_name)

    def delete_ssh_key(self, ssh_key_name):
        self._client.delete_key_pair(KeyName=ssh_key_name)
