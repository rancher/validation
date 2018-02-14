from common import *
from lib.aws import AmazonWebServices

AGENT_REG_CMD = os.environ.get('RANCHER_AGENT_REG_CMD', "")
HOST_COUNT = int(os.environ.get('RANCHER_HOST_COUNT', 1))


def test_add_custom_host():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes\
            (HOST_COUNT, random_test_name("testsahost"))
    if AGENT_REG_CMD != "":
        for aws_node in aws_nodes:
            aws_node.execute_command(AGENT_REG_CMD)