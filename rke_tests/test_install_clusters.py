from conftest import *  # NOQA
from common import *


def test_cluster_install_roles_1(
        test_name, cloud_provider, rke_client, kubectl):
    # Create minimal cluster, one node with all three roles
    rke_template = 'cluster_install_roles_1.yml.j2'
    nodes = cloud_provider.create_multiple_nodes(1, test_name)
    create_rke_cluster(rke_client, kubectl, nodes, rke_template)
    validate_rke_cluster(rke_client, kubectl, nodes)
    for node in nodes:
        cloud_provider.delete_node(node)


def test_cluster_install_roles_2(
        test_name, cloud_provider, rke_client, kubectl):
    """
    Create three node cluster, one node with all three roles,
    other 2 worker nodes
    """
    rke_template = 'cluster_install_roles_2.yml.j2'
    nodes = cloud_provider.create_multiple_nodes(3, test_name)
    create_rke_cluster(rke_client, kubectl, nodes, rke_template)
    validate_rke_cluster(rke_client, kubectl, nodes)
    for node in nodes:
        cloud_provider.delete_node(node)
