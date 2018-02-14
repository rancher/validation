from common import *
from lib.aws import AmazonWebServices
import pytest

DO_ACCESSKEY = os.environ.get('DO_ACCESSKEY', "None")
MACHINE_TIMEOUT = os.environ.get('MACHINE_TIMEOUT', "1200")

rke_config = {"authentication": {"type": "authnConfig", "strategy": "x509"},
              "ignoreDockerVersion": False,
              "network": {"type": "networkConfig", "plugin": "canal"},
              "type": "rancherKubernetesEngineConfig"
              }

if_stress_enabled = pytest.mark.skipif(
    not os.environ.get('RANCHER_STRESS_TEST_WORKER_COUNT'),
    reason='Stress test not enabled')

worker_count = int(os.environ.get('RANCHER_STRESS_TEST_WORKER_COUNT', 1))
m_timeout = int(MACHINE_TIMEOUT)
RANCHER_CLEANUP_CLUSTER = os.environ.get('RANCHER_CLEANUP_CLUSTER', "True")


def test_rke_do_host_1(node_template_do):
    client = get_admin_client()
    nodes = []
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template_do.id,
            "requestedHostname": node_name,
            "controlPlane": True,
            "etcd": True,
            "worker": True,
            "quantity": 1,
            "clusterId": None}
    nodes.append(node)
    cluster, node_pools = create_and_vaildate_cluster(client, nodes)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)


def test_rke_do_host_2(node_template_do):
    client = get_admin_client()
    nodes = []
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template_do.id,
            "requestedHostname": node_name,
            "controlPlane": True,
            "quantity": 1}
    nodes.append(node)
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template_do.id,
            "requestedHostname": node_name,
            "etcd": True,
            "quantity": 1}
    nodes.append(node)
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template_do.id,
            "requestedHostname": node_name,
            "worker": True,
            "quantity": 3}
    nodes.append(node)
    cluster, node_pools = create_and_vaildate_cluster(client, nodes)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)


def test_rke_do_host_3(node_template_do):
    client = get_admin_client()
    nodes = []
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template_do.id,
            "requestedHostname": node_name,
            "controlPlane": True,
            "quantity": 2}
    nodes.append(node)
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template_do.id,
            "requestedHostname": node_name,
            "etcd": True,
            "quantity": 3}
    nodes.append(node)
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template_do.id,
            "requestedHostname": node_name,
            "worker": True,
            "quantity": 3}
    nodes.append(node)
    cluster, node_pools = create_and_vaildate_cluster(client, nodes)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)


@pytest.mark.skip("reason for skipping")
def test_rke_do_host_4(node_template_do):
    client = get_admin_client()

    # Create cluster and add a node pool to this cluster
    nodes = []
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template_do.id,
            "requestedHostname": node_name,
            "controlPlane": True,
            "etcd": True,
            "worker": True,
            "quantity": 1}
    nodes.append(node)
    cluster, node_pools = create_and_vaildate_cluster(client, nodes)
    assert len(cluster.nodes()) == 1
    node1 = cluster.nodes()[0]
    assert len(node_pools) == 1
    node_pool = node_pools[0]

    # Increase the scale of the node pool to 3
    node_pool = client.update(node_pool, quantity=3)
    """
    for node in node_pool.nodes():
        node = client.wait_success(node, timeout=m_timeout)
        assert node.state == "active"
    assert len(node_pool.nodes()) == 3
    """
    cluster = validate_cluster(client, cluster, check_intermediate_state=False)
    nodes = client.list_node(clusterId=cluster.id)
    assert len(nodes) == 3

    # Delete node1
    node1 = client.delete(node1)
    cluster = validate_cluster(client, cluster, check_intermediate_state=False)
    nodes = client.list_node(clusterId=cluster.id)
    assert len(nodes) == 2
    delete_cluster(client, cluster)


def test_rke_custom_host_docker_1():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes\
            (1, random_test_name("testcustom"))
    aws_node = aws_nodes[0]
    node_roles = ["worker", "controlplane", "etcd"]

    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    docker_run_cmd = \
        get_custom_host_registration_cmd(client, cluster, node_roles)
    aws_node.execute_command(docker_run_cmd)
    cluster = validate_cluster(client, cluster)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)



def test_rke_custom_host_docker_2():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes\
            (5, random_test_name("testcustom"))
    node_roles = [["controlplane"], ["etcd"],
                  ["worker"],["worker"],["worker"]]

    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    i = 0
    for aws_node in aws_nodes:
        docker_run_cmd = \
            get_custom_host_registration_cmd(client, cluster, node_roles[i])
        aws_node.execute_command(docker_run_cmd)
        i += 1
    cluster = validate_cluster(client, cluster)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)


def test_rke_custom_host_docker_3():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes\
            (8, random_test_name("testcustom"))
    node_roles = [
                     ["controlplane"], ["controlplane"],
                     ["etcd"], ["etcd"], ["etcd"],
                     ["worker"], ["worker"], ["worker"]
                  ]
    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    i = 0
    for aws_node in aws_nodes:
        docker_run_cmd = \
            get_custom_host_registration_cmd(client, cluster, node_roles[i])
        aws_node.execute_command(docker_run_cmd)
        i += 1
    cluster = validate_cluster(client, cluster)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)


@if_stress_enabled
def test_rke_custom_host_stress():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes\
            (worker_count + 4, random_test_name("teststress"))
    node_roles = [["controlplane"], ["etcd"], ["etcd"], ["etcd"]]
    worker_role = ["worker"]
    for int in range(0, worker_count):
        node_roles.append(worker_role)
    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    i = 0
    for aws_node in aws_nodes:
        docker_run_cmd = \
            get_custom_host_registration_cmd(client, cluster, node_roles[i])
        aws_node.execute_command(docker_run_cmd)
        i += 1
    cluster = validate_cluster(client, cluster)


@pytest.mark.skip("reason for skipping")
def test_rke_custom_host_docker_4():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes\
            (2, random_test_name("testcustom"))
    aws_node = aws_nodes[0]
    node_roles = ["worker", "controlplane", "etcd"]

    # Add node1 to cluster

    client = get_admin_client()
    cluster = client.create_cluster(name=random_name())
    assert cluster.state == "active"
    docker_run_cmd = \
        get_custom_host_registration_cmd(client, cluster, node_roles)
    aws_node.execute_command(docker_run_cmd)
    validate_cluster(client, cluster)
    nodes = client.list_nodes(clusterId=cluster.id)
    assert len(nodes) == 1
    node1 = nodes[0]
    assert nodes[0]["requestedHostname"] == aws_nodes[0].host_name
    assert nodes[0]

    # Add node2 to cluster
    aws_node = aws_nodes[1]
    docker_run_cmd = get_custom_host_registration_cmd(client, cluster, node_roles)
    aws_node.execute_command(docker_run_cmd)
    validate_cluster(client, cluster, check_intermediate_state=False)

    nodes = client.list_nodes(clusterId=cluster.id)
    assert len(nodes) == 2

    # Delete node1
    node1 = client.delete(node1)
    validate_cluster(client, cluster, check_intermediate_state=False)
    nodes = client.list_nodes(clusterId=cluster.id)
    assert len(nodes) == 1
    assert nodes[0]["requestedHostname"] == aws_nodes[1].host_name

    delete_cluster(client, cluster)
    delete_node(aws_nodes)


def create_and_vaildate_cluster(client, nodes,
                                rancherKubernetesEngineConfig=rke_config):
    cluster = client.create_cluster(
        name=random_name(),
        rancherKubernetesEngineConfig=rancherKubernetesEngineConfig)
    node_pools =[]
    for node in nodes:
        node["clusterId"] = cluster.id
        node_pool = client.create_node_pool(**node)
        node_pool = client.wait_success(node_pool)
        node_pools.append(node_pool)

    cluster = validate_cluster(client, cluster)
    nodes = client.list_node(clusterId=cluster.id)
    assert len(nodes) == len(nodes)
    for node in nodes:
        assert node.state == "active"
    expected_host_names = []

    for node in nodes:
        expected_host_names.append(node["requestedHostname"])
    for node in nodes:
        assert node["requestedHostname"] in expected_host_names
        i = expected_host_names.index(node["requestedHostname"])
        del expected_host_names[i]
    assert len(expected_host_names) == 0
    return cluster, node_pools


def validate_cluster(client, cluster, intermediate_state="provisioning",
                     check_intermediate_state=True):
    if check_intermediate_state:
        cluster= wait_for_condition(
            client, cluster,
            lambda x: x.state == intermediate_state,
            lambda x: 'State is: ' + x.state,
            timeout=m_timeout)
        assert cluster.state == intermediate_state
    cluster = wait_for_condition(
        client, cluster,
        lambda x: x.state == "active",
        lambda x: 'State is: ' + x.state,
        timeout=m_timeout)
    assert cluster.state == "active"
    wait_for_nodes_to_become_active(client, cluster)
    create_project_and_ns(ADMIN_TOKEN, cluster)
    return cluster


def wait_for_nodes_to_become_active(client, cluster):
    nodes = client.list_node(clusterId=cluster.id)
    assert len(nodes) == len(nodes)
    for node in nodes:
        node = wait_for_condition(
            client, node,
            lambda x: x.state == "active",
            lambda x: 'State is: ' + x.state,
            timeout=m_timeout)


def random_name():
    return "test" + "-" + str(random_int(10000, 99999))


@pytest.fixture(scope='session')
def node_template_do():
    client = get_admin_client()
    node_template = client.create_node_template(
        digitaloceanConfig={"accessToken":DO_ACCESSKEY,
                            "region": "nyc3",
                            "size": "1gb",
                            "image": "ubuntu-16-04-x64"},
        name=random_name(),
        driver="digitalocean",
        namespaceId="fixme",
        useInternalIpAddress=True)
    node_template= client.wait_success(node_template)
    return node_template


def delete_node(aws_nodes):
    for node in aws_nodes:
        AmazonWebServices().delete_node(node)


def delete_cluster(client, cluster):
    # Delete Cluster
    client.delete(cluster)
    """
    cluster = wait_for_condition(
        client, cluster,
        lambda x: x.state == "removed",
        lambda x: 'State is: ' + x.state,
        timeout=m_timeout)
    assert cluster.state == "removed"
    """
    

def get_custom_host_registration_cmd(client, cluster, roles):
    allowed_roles = ["etcd", "worker", "controlplane"]
    cluster_tokens = client.list_cluster_registration_token(clusterId=cluster.id)
    if len(cluster_tokens) > 0:
        cluster_token = cluster_tokens[0]
    else:
        cluster_token = create_custom_host_registration_token(client, cluster)
    cmd = cluster_token.nodeCommand
    for role in roles:
        assert role in allowed_roles
        cmd += " --"+role
    return cmd


def create_custom_host_registration_token(client, cluster):
    cluster_token = client.create_cluster_registration_token(clusterId=cluster.id)
    cluster_token = client.wait_success(cluster_token)
    assert cluster_token.state == 'active'
    return cluster_token
