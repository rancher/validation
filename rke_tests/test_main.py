from conftest import *  # NOQA


def test_main(cloud_provider, rke_client):
    ssh_key_name = 'mykeyfornode'
    node_name = 'pytest-1234-main-test-node0'
    rke_template = 'minimal_cluster_template.yml.j2'

    # create node from cloud provider
    node = cloud_provider.create_node(
        node_name, ssh_key_name, wait_for_ready=True)

    # create rke cluster yml
    config_yml = rke_client.build_rke_template(
        rke_template, [node], master_ssh_key_path=node.ssh_key_path)

    # run rke up
    result = rke_client.up(config_yml)
    assert result.ok, result.stderr

    # validate k8s reachable
    kube_config = rke_client.get_kube_config_for_config()
    print kube_config

    # clean up node(s)
    cloud_provider.delete_node(node, wait_for_deleted=True)
