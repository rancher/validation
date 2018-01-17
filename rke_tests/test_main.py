from conftest import *  # NOQA


def test_minimal_cluster(test_name, cloud_provider, rke_client, kubectl):
    node_name = '{}-node0'.format(test_name)
    rke_template = 'minimal_cluster_template.yml.j2'

    # create node from cloud provider
    node = cloud_provider.create_node(node_name, wait_for_ready=True)

    # create rke cluster yml
    config_yml = rke_client.build_rke_template(
        rke_template, [node], master_ssh_key_path=node.ssh_key_path)

    print config_yml
    # run rke up
    result = rke_client.up(config_yml)
    assert result.ok, result.stderr

    # validate k8s reachable
    kube_config = rke_client.get_kube_config_for_config()
    print kube_config

    #
    kubectl.kube_config_path = rke_client.kube_config_path()
    result = kubectl.create_validation_stack(
        input_config={'namespace': 'main', 'port_ext': '01'})

    # clean up node(s)
    # cloud_provider.delete_node(node, wait_for_deleted=True)


def test_multiple_nodes_cluster(test_name, cloud_provider, rke_client, kubectl):
    node_name = '{}-node'.format(test_name)
    rke_template = 'cluster_3node_template.yml.j2'

    # create node from cloud provider
    nodes = cloud_provider.create_multiple_nodes(
        3, node_name, wait_for_ready=True)

    # create rke cluster yml
    config_yml = rke_client.build_rke_template(
        rke_template, nodes, master_ssh_key_path=node.ssh_key_path)

    # run rke up
    result = rke_client.up(config_yml)
    assert result.ok, result.stderr

    # validate k8s reachable
    kube_config = rke_client.get_kube_config_for_config()
    print kube_config

    #
    kubectl.kube_config_path = rke_client.kube_config_path()
    result = kubectl.create_validation_stack(
        input_config={'namespace': 'main', 'port_ext': '01'})

    # clean up node(s)
    # cloud_provider.delete_node(node, wait_for_deleted=True)