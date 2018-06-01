from common import *   # NOQA
from lib.aws import AmazonWebServices

AGENT_REG_CMD = os.environ.get('RANCHER_AGENT_REG_CMD', "")
HOST_COUNT = int(os.environ.get('RANCHER_HOST_COUNT', 1))
HOST_NAME = os.environ.get('RANCHER_HOST_NAME', "testsa")
RANCHER_SERVER_VERSION = os.environ.get('RANCHER_SERVER_VERSION', "master")


def test_add_custom_host():
    aws_nodes = AmazonWebServices().create_multiple_nodes(
        HOST_COUNT, random_test_name("testsa"+HOST_NAME))
    if AGENT_REG_CMD != "":
        for aws_node in aws_nodes:
            aws_node.execute_command(AGENT_REG_CMD)


def test_deploy_rancher_server():
    RANCHER_SERVER_CMD = \
        "docker run -d --restart=unless-stopped -p 80:80 -p 443:443 " + \
        "rancher/rancher"
    RANCHER_SERVER_CMD += ":" + RANCHER_SERVER_VERSION
    aws_nodes = AmazonWebServices().create_multiple_nodes(
        1, random_test_name("testsa"+HOST_NAME))
    aws_nodes[0].execute_command(RANCHER_SERVER_CMD)
