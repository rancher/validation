import time

from conftest import *  # NOQA


def test_main(cloud_provider, rke_client):
    ssh_key_name = 'mykeyfornode'
    node_name = 'pytest-1234-main-test-node0'
    rke_template = 'minimal_cluster_template.yml.j2'
    rke_yaml = 'cluster.yml'
    # create key(s)
    public_ssh_key = cloud_provider.generate_ssh_key(ssh_key_name)

    # import ssh key(s) to cloud provider
    cloud_provider.import_ssh_key(ssh_key_name, public_ssh_key)

    # create node from cloud provider
    node = cloud_provider.create_node(
        node_name, ssh_key_name, wait_for_ready=True)

    # create rke cluster yml
    config_yml = rke_client.build_rke_template(
        rke_template, [node], master_ssh_key_path=node.ssh_key_path)
    rke_client.save_cluster_yml(rke_yaml, config_yml)

    # run rke up
    result = rke_client.up(config=rke_yaml)
    assert result.ok, result.stderr

    # validate k8s reachable
    kube_config = rke_client.get_kube_config_for_config(rke_yaml)
    print kube_config

    # clean up node(s)
    cloud_provider.delete_node(node, wait_for_deleted=True)


