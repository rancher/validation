from conftest import *  # NOQA
from common import *


def test_cluster_update_roles_1(
        test_name, cloud_provider, rke_client, kubectl):
    """
    Create three node cluster, each node with a single role
    node0 - controlplace
    node1 - worker
    node2 - etcd
    validates cluster, leaves ns/pods intact
    Adds a worker
    node0 - controlplace
    node1 - worker
    node2 - etcd
    node3 - worker
    """
    rke_template = 'cluster_update_roles_1_1.yml.j2'
    all_nodes = cloud_provider.create_multiple_nodes(4, test_name)
    before_update_nodes = all_nodes[0:-1]  # only use three nodes at first
    create_rke_cluster(rke_client, kubectl, before_update_nodes, rke_template)
    network, dns_discovery = validate_rke_cluster(
        rke_client, kubectl, before_update_nodes, 'beforeupdate')

    # New cluster needs to keep controlplane and etcd nodes the same
    rke_template = 'cluster_update_roles_1_2.yml.j2'
    create_rke_cluster(rke_client, kubectl, all_nodes, rke_template)
    # rerun validation on existing validation resources
    validate_rke_cluster(
        rke_client, kubectl, all_nodes, 'beforeupdate',
        network_validation=network, dns_validation=dns_discovery)

    network, dns_discovery = validate_rke_cluster(
        rke_client, kubectl, all_nodes, 'afterupdate')
    for node in all_nodes:
        cloud_provider.delete_node(node)
