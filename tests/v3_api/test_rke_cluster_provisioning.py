from common import *   # NOQA
from lib.aws import AmazonWebServices
import pytest
from threading import Thread


DO_ACCESSKEY = os.environ.get('DO_ACCESSKEY', "None")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION")
AWS_SUBNET = os.environ.get("AWS_SUBNET")
AWS_VPC = os.environ.get("AWS_VPC")
AWS_SG = os.environ.get("AWS_SG")
AWS_ZONE = os.environ.get("AWS_ZONE")
AWS_IAM_PROFILE = os.environ.get("AWS_IAM_PROFILE", "")
AZURE_SUBSCRIPTION_ID = os.environ.get("AZURE_SUBSCRIPTION_ID")
AZURE_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.environ.get("AZURE_TENANT_ID")

engine_install_url = "https://releases.rancher.com/install-docker/17.03.sh"
rke_config = {"authentication": {"type": "authnConfig", "strategy": "x509"},
              "ignoreDockerVersion": False,
              "network": {"type": "networkConfig", "plugin": "canal"},
              "type": "rancherKubernetesEngineConfig"
              }

rke_config_aws_provider = {"authentication": {"type": "authnConfig",
                                              "strategy": "x509"},
                           "ignoreDockerVersion": False,
                           "network": {"type": "networkConfig",
                                       "plugin": "canal"},
                           "type": "rancherKubernetesEngineConfig",
                           "cloudProvider": {"name": "aws",
                                             "type": "cloudProvider",
                                             "awsCloudProvider":
                                                 {"type": "awsCloudProvider"}}
                           }


rke_config_azure_provider = {"authentication": {"type": "authnConfig",
                                                "strategy": "x509"},
                             "ignoreDockerVersion": False,
                             "network": {"type": "networkConfig",
                                         "plugin": "canal"},
                             "type": "rancherKubernetesEngineConfig",
                             "cloudProvider": {
                             "type": "cloudProvider",
                             "name": "azure",
                             "azureCloudProvider": {
                                 "aadClientId": AZURE_CLIENT_ID,
                                 "aadClientSecret": AZURE_CLIENT_SECRET,
                                 "subscriptionId": AZURE_SUBSCRIPTION_ID,
                                 "tenantId": AZURE_TENANT_ID}}
                             }

if_stress_enabled = pytest.mark.skipif(
    not os.environ.get('RANCHER_STRESS_TEST_WORKER_COUNT'),
    reason='Stress test not enabled')

worker_count = int(os.environ.get('RANCHER_STRESS_TEST_WORKER_COUNT', 1))
RANCHER_CLEANUP_CLUSTER = os.environ.get('RANCHER_CLEANUP_CLUSTER', "True")


def test_rke_az_host_1(node_template_az):
    validate_rke_dm_host_1(node_template_az, rke_config)


def test_rke_az_host_2(node_template_az):
    validate_rke_dm_host_2(node_template_az, rke_config)


def test_rke_az_host_3(node_template_az):
    validate_rke_dm_host_3(node_template_az, rke_config)


def test_rke_az_host_4(node_template_az):
    validate_rke_dm_host_4(node_template_az, rke_config)


def test_rke_az_host_with_provider_1(node_template_az):
    validate_rke_dm_host_1(node_template_az, rke_config_azure_provider)


def test_rke_az_host_with_provider_2(node_template_az):
    validate_rke_dm_host_2(node_template_az, rke_config_azure_provider)


def test_rke_do_host_1(node_template_do):
    validate_rke_dm_host_1(node_template_do, rke_config)


def test_rke_do_host_2(node_template_do):
    validate_rke_dm_host_2(node_template_do, rke_config)


def test_rke_do_host_3(node_template_do):
    validate_rke_dm_host_3(node_template_do, rke_config)


def test_rke_do_host_4(node_template_do):
    validate_rke_dm_host_4(node_template_do, rke_config)


def test_rke_ec2_host_1(node_template_ec2):
    validate_rke_dm_host_1(node_template_ec2, rke_config)


def test_rke_ec2_host_2(node_template_ec2):
    validate_rke_dm_host_2(node_template_ec2, rke_config)


def test_rke_ec2_host_3(node_template_ec2):
    validate_rke_dm_host_3(node_template_ec2, rke_config)


def test_rke_ec2_host_with_aws_provider_1(node_template_ec2_with_provider):
    validate_rke_dm_host_1(node_template_ec2_with_provider,
                           rke_config_aws_provider)


def test_rke_ec2_host_with_aws_provider_2(node_template_ec2_with_provider):
    validate_rke_dm_host_2(node_template_ec2_with_provider,
                           rke_config_aws_provider)


def test_rke_ec2_host_4(node_template_ec2):
    validate_rke_dm_host_4(node_template_ec2, rke_config)


def test_rke_custom_host_1():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes(
            1, random_test_name("testcustom"))
    node_roles = ["worker", "controlplane", "etcd"]

    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    for aws_node in aws_nodes:
        docker_run_cmd = \
            get_custom_host_registration_cmd(client, cluster, node_roles,
                                             aws_node)
        aws_node.execute_command(docker_run_cmd)
    cluster = validate_cluster(client, cluster)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)


def test_rke_custom_host_2():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes(
            5, random_test_name("testcustom"))
    node_roles = [["controlplane"], ["etcd"],
                  ["worker"], ["worker"], ["worker"]]

    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    i = 0
    for aws_node in aws_nodes:
        docker_run_cmd = \
            get_custom_host_registration_cmd(client, cluster, node_roles[i],
                                             aws_node)
        aws_node.execute_command(docker_run_cmd)
        i += 1
    cluster = validate_cluster(client, cluster)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)


def test_rke_custom_host_3():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes(
            8, random_test_name("testcustom"))
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
            get_custom_host_registration_cmd(client, cluster, node_roles[i],
                                             aws_node)
        aws_node.execute_command(docker_run_cmd)
        i += 1
    cluster = validate_cluster(client, cluster)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)


def test_rke_custom_host_4():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes(
            8, random_test_name("testcustom"))
    node_roles = [
        {"roles": ["controlplane"],
         "nodes":[aws_nodes[0], aws_nodes[1]]},
        {"roles": ["etcd"],
         "nodes": [aws_nodes[2], aws_nodes[3], aws_nodes[4]]},
        {"roles": ["worker"],
         "nodes": [aws_nodes[5], aws_nodes[6], aws_nodes[7]]}
    ]
    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    delay = 120
    host_threads = []
    for node_role in node_roles:
        host_thread = Thread(target=register_host_after_delay,
                             args=(client, cluster, node_role, delay))
        host_threads.append(host_thread)
        host_thread.start()
        time.sleep(30)
    for host_thread in host_threads:
        host_thread.join()
    cluster = validate_cluster(client, cluster,
                               check_intermediate_state=False)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)


@if_stress_enabled
def test_rke_custom_host_stress():
    aws_nodes = AmazonWebServices().create_multiple_nodes(
        worker_count + 4, random_test_name("teststress"))

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
            get_custom_host_registration_cmd(client, cluster, node_roles[i],
                                             aws_node)
        aws_node.execute_command(docker_run_cmd)
        i += 1
    cluster = validate_cluster(client, cluster)


def test_rke_custom_host_etcd_plane_changes():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes(
            7, random_test_name("testcustom"))
    node_roles = [["controlplane"], ["etcd"],
                  ["worker"], ["worker"], ["worker"]]

    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    i = 0
    for i in range(0, 5):
        aws_node = aws_nodes[i]
        docker_run_cmd = \
            get_custom_host_registration_cmd(client, cluster, node_roles[i],
                                             aws_node)
        aws_node.execute_command(docker_run_cmd)
    cluster = validate_cluster(client, cluster)
    etcd_nodes = get_role_nodes(cluster, "etcd")
    assert len(etcd_nodes) == 1

    # Add 1 more etcd node
    aws_node = aws_nodes[5]
    docker_run_cmd = get_custom_host_registration_cmd(client, cluster,
                                                      ["etcd"], aws_node)
    aws_node.execute_command(docker_run_cmd)
    wait_for_cluster_node_count(client, cluster, 6)
    validate_cluster(client, cluster, intermediate_state="updating")

    # Add 1 more etcd node
    aws_node = aws_nodes[6]
    docker_run_cmd = get_custom_host_registration_cmd(client, cluster,
                                                      ["etcd"], aws_node)
    aws_node.execute_command(docker_run_cmd)
    wait_for_cluster_node_count(client, cluster, 7)
    validate_cluster(client, cluster, intermediate_state="updating")

    # Delete the first etcd node
    client.delete(etcd_nodes[0])
    validate_cluster(client, cluster, intermediate_state="updating")

    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)


def test_rke_custom_host_etcd_plane_changes_1():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes(
            7, random_test_name("testcustom"))
    node_roles = [["controlplane"], ["etcd"],
                  ["worker"], ["worker"], ["worker"]]

    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    i = 0
    for i in range(0, 5):
        aws_node = aws_nodes[i]
        docker_run_cmd = \
            get_custom_host_registration_cmd(client, cluster,
                                             node_roles[i], aws_node)
        aws_node.execute_command(docker_run_cmd)
    cluster = validate_cluster(client, cluster)
    etcd_nodes = get_role_nodes(cluster, "etcd")
    assert len(etcd_nodes) == 1

    # Add 2 more etcd node
    aws_node = aws_nodes[5]
    docker_run_cmd = get_custom_host_registration_cmd(client, cluster,
                                                      ["etcd"], aws_node)
    aws_node.execute_command(docker_run_cmd)

    aws_node = aws_nodes[6]
    docker_run_cmd = get_custom_host_registration_cmd(client, cluster,
                                                      ["etcd"], aws_node)
    aws_node.execute_command(docker_run_cmd)

    wait_for_cluster_node_count(client, cluster, 7)
    validate_cluster(client, cluster, intermediate_state="updating")
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)


def test_rke_custom_host_control_plane_changes():
    aws_nodes = \
        aws_nodes = \
        AmazonWebServices().create_multiple_nodes(
            6, random_test_name("testcustom"))

    node_roles = [["controlplane"], ["etcd"],
                  ["worker"], ["worker"], ["worker"]]

    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    i = 0
    for i in range(0, 5):
        aws_node = aws_nodes[i]
        docker_run_cmd = \
            get_custom_host_registration_cmd(client, cluster,
                                             node_roles[i], aws_node)
        aws_node.execute_command(docker_run_cmd)
    cluster = validate_cluster(client, cluster)
    control_nodes = get_role_nodes(cluster, "control")
    assert len(control_nodes) == 1

    # Add 1 more control node
    aws_node = aws_nodes[5]
    docker_run_cmd = get_custom_host_registration_cmd(client, cluster,
                                                      ["controlplane"],
                                                      aws_node)
    aws_node.execute_command(docker_run_cmd)
    wait_for_cluster_node_count(client, cluster, 6)
    validate_cluster(client, cluster, intermediate_state="updating")

    # Delete the first control node
    client.delete(control_nodes[0])
    validate_cluster(client, cluster, intermediate_state="updating")

    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)


def test_rke_custom_host_worker_plane_changes():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes(
            4, random_test_name("testcustom"))
    node_roles = [["controlplane"], ["etcd"],
                  ["worker"]]

    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    i = 0
    for i in range(0, 3):
        aws_node = aws_nodes[i]
        docker_run_cmd = \
            get_custom_host_registration_cmd(client, cluster, node_roles[i],
                                             aws_node)
        aws_node.execute_command(docker_run_cmd)
    cluster = validate_cluster(client, cluster)
    worker_nodes = get_role_nodes(cluster, "worker")
    assert len(worker_nodes) == 1

    # Add 1 more worker node
    aws_node = aws_nodes[3]
    docker_run_cmd = get_custom_host_registration_cmd(client, cluster,
                                                      ["worker"], aws_node)
    aws_node.execute_command(docker_run_cmd)
    wait_for_cluster_node_count(client, cluster, 4)
    validate_cluster(client, cluster, check_intermediate_state=False)

    # Delete the first worker node
    client.delete(worker_nodes[0])
    validate_cluster(client, cluster, check_intermediate_state=False)

    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)


def test_rke_custom_control_node_power_down():
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes(
            5, random_test_name("testcustom"))
    node_roles = [["controlplane"], ["etcd"],
                  ["worker"]]

    client = get_admin_client()
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    i = 0
    for i in range(0, 3):
        aws_node = aws_nodes[i]
        docker_run_cmd = \
            get_custom_host_registration_cmd(client, cluster, node_roles[i],
                                             aws_node)
        aws_node.execute_command(docker_run_cmd)
    cluster = validate_cluster(client, cluster)
    control_nodes = get_role_nodes(cluster, "control")
    assert len(control_nodes) == 1

    # Add 1 more control node
    aws_node = aws_nodes[3]
    docker_run_cmd = get_custom_host_registration_cmd(client, cluster,
                                                      ["controlplane"],
                                                      aws_node)
    aws_node.execute_command(docker_run_cmd)
    wait_for_cluster_node_count(client, cluster, 4)
    validate_cluster(client, cluster, check_intermediate_state=False)

    # Power Down the first control node
    aws_control_node = aws_nodes[0]
    AmazonWebServices().stop_node(aws_control_node, wait_for_stopped=True)
    control_node = control_nodes[0]
    wait_for_node_status(client, control_node, "unavailable")
    validate_cluster(
        client, cluster,
        check_intermediate_state=False,
        nodes_not_in_active_state=[control_node.requestedHostname])

    # Add 1 more worker node
    aws_node = aws_nodes[4]
    docker_run_cmd = get_custom_host_registration_cmd(client, cluster,
                                                      ["worker"], aws_node)
    aws_node.execute_command(docker_run_cmd)
    wait_for_cluster_node_count(client, cluster, 4)
    validate_cluster(client, cluster, check_intermediate_state=False)

    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)
        delete_node(aws_nodes)


def validate_rke_dm_host_1(node_template,
                           rancherKubernetesEngineConfig=rke_config):
    client = get_admin_client()
    nodes = []
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template.id,
            "requestedHostname": node_name,
            "controlPlane": True,
            "etcd": True,
            "worker": True,
            "quantity": 1,
            "clusterId": None}
    nodes.append(node)
    cluster, node_pools = create_and_vaildate_cluster(
        client, nodes, rancherKubernetesEngineConfig)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)


def validate_rke_dm_host_2(node_template,
                           rancherKubernetesEngineConfig=rke_config):
    client = get_admin_client()
    nodes = []
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template.id,
            "requestedHostname": node_name,
            "controlPlane": True,
            "quantity": 1}
    nodes.append(node)
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template.id,
            "requestedHostname": node_name,
            "etcd": True,
            "quantity": 1}
    nodes.append(node)
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template.id,
            "requestedHostname": node_name,
            "worker": True,
            "quantity": 3}
    nodes.append(node)
    cluster, node_pools = create_and_vaildate_cluster(
        client, nodes, rancherKubernetesEngineConfig)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)


def validate_rke_dm_host_3(node_template,
                           rancherKubernetesEngineConfig=rke_config):
    client = get_admin_client()
    nodes = []
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template.id,
            "requestedHostname": node_name,
            "controlPlane": True,
            "quantity": 2}
    nodes.append(node)
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template.id,
            "requestedHostname": node_name,
            "etcd": True,
            "quantity": 3}
    nodes.append(node)
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template.id,
            "requestedHostname": node_name,
            "worker": True,
            "quantity": 3}
    nodes.append(node)
    cluster, node_pools = create_and_vaildate_cluster(
        client, nodes, rancherKubernetesEngineConfig)
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)


def validate_rke_dm_host_4(node_template,
                           rancherKubernetesEngineConfig=rke_config):
    client = get_admin_client()

    # Create cluster and add a node pool to this cluster
    nodes = []
    node_name = random_name()
    node = {"hostnamePrefix": node_name,
            "nodeTemplateId": node_template.id,
            "requestedHostname": node_name,
            "controlPlane": True,
            "etcd": True,
            "worker": True,
            "quantity": 1}
    nodes.append(node)
    cluster, node_pools = create_and_vaildate_cluster(
        client, nodes, rancherKubernetesEngineConfig)
    assert len(cluster.nodes()) == 1
    node1 = cluster.nodes()[0]
    assert len(node_pools) == 1
    node_pool = node_pools[0]

    # Increase the scale of the node pool to 3
    node_pool = client.update(node_pool, quantity=3)
    cluster = validate_cluster(client, cluster, intermediate_state="updating")
    nodes = client.list_node(clusterId=cluster.id)
    assert len(nodes) == 3

    # Delete node1
    node1 = client.delete(node1)
    wait_for_node_to_be_deleted(client, node1)

    cluster = validate_cluster(client, cluster, intermediate_state="updating")
    nodes = client.list_node(clusterId=cluster.id)
    assert len(nodes) == 3
    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)


def create_and_vaildate_cluster(client, nodes,
                                rancherKubernetesEngineConfig=rke_config):
    cluster = client.create_cluster(
        name=random_name(),
        rancherKubernetesEngineConfig=rancherKubernetesEngineConfig)
    node_pools = []
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


def random_name():
    return "test" + "-" + str(random_int(10000, 99999))


@pytest.fixture(scope='session')
def node_template_az():
    client = get_admin_client()
    azConfig = {
        "availabilitySet": "docker-machine",
        "clientId": AZURE_CLIENT_ID,
        "clientSecret": AZURE_CLIENT_SECRET,
        "customData": "",
        "dns": "",
        "dockerPort": "2376",
        "environment": "AzurePublicCloud",
        "image": "canonical:UbuntuServer:16.04.0-LTS:latest",
        "location": "westus",
        "noPublicIp": False,
        "openPort": [
            "6443/tcp",
            "2379/tcp",
            "2380/tcp",
            "8472/udp",
            "4789/udp",
            "10256/tcp",
            "10250/tcp",
            "10251/tcp",
            "10252/tcp",
            "80/tcp",
            "443/tcp"
        ],
        "privateIpAddress": "",
        "resourceGroup": "docker-machine",
        "size": "Standard_A2",
        "sshUser": "docker-user",
        "staticPublicIp": False,
        "storageType": "Standard_LRS",
        "subnet": "docker-machine",
        "subnetPrefix": "192.168.0.0/16",
        "subscriptionId": AZURE_SUBSCRIPTION_ID,
        "usePrivateIp": False,
        "vnet": "docker-machine-vnet"
    }
    node_template = client.create_node_template(
        azureConfig=azConfig,
        name=random_name(),
        driver="azure",
        namespaceId="fixme",
        useInternalIpAddress=True)
    node_template = client.wait_success(node_template)
    return node_template


@pytest.fixture(scope='session')
def node_template_do():
    client = get_admin_client()
    node_template = client.create_node_template(
        digitaloceanConfig={"accessToken": DO_ACCESSKEY,
                            "region": "nyc3",
                            "size": "s-2vcpu-2gb",
                            "image": "ubuntu-16-04-x64"},
        name=random_name(),
        driver="digitalocean",
        namespaceId="fixme",
        useInternalIpAddress=True)
    node_template = client.wait_success(node_template)
    return node_template


@pytest.fixture(scope='session')
def node_template_ec2():
    client = get_admin_client()
    amazonec2Config = {
        "accessKey": AWS_ACCESS_KEY_ID,
        "instanceType": "t2.medium",
        "region": AWS_REGION,
        "rootSize": "16",
        "secretKey": AWS_SECRET_ACCESS_KEY,
        "securityGroup": [AWS_SG],
        "sshUser": "ubuntu",
        "subnetId": AWS_SUBNET,
        "usePrivateAddress": False,
        "volumeType": "gp2",
        "vpcId": AWS_VPC,
        "zone": AWS_ZONE
    }

    node_template = client.create_node_template(
        amazonec2Config=amazonec2Config,
        name=random_name(),
        namespaceId="fixme",
        useInternalIpAddress=True,
        driver="amazonec2",
        engineInstallURL=engine_install_url
    )
    node_template = client.wait_success(node_template)
    return node_template


@pytest.fixture(scope='session')
def node_template_ec2_with_provider():
    client = get_admin_client()
    amazonec2Config = {
        "accessKey": AWS_ACCESS_KEY_ID,
        "instanceType": "t2.medium",
        "region": AWS_REGION,
        "rootSize": "16",
        "secretKey": AWS_SECRET_ACCESS_KEY,
        "securityGroup": [AWS_SG],
        "sshUser": "ubuntu",
        "subnetId": AWS_SUBNET,
        "usePrivateAddress": False,
        "volumeType": "gp2",
        "vpcId": AWS_VPC,
        "zone": AWS_ZONE,
        "iamInstanceProfile": AWS_IAM_PROFILE
    }

    node_template = client.create_node_template(
        amazonec2Config=amazonec2Config,
        name=random_name(),
        namespaceId="fixme",
        useInternalIpAddress=True,
        driver="amazonec2",
        engineInstallURL=engine_install_url
    )
    node_template = client.wait_success(node_template)
    return node_template


def delete_node(aws_nodes):
    for node in aws_nodes:
        AmazonWebServices().delete_node(node)


def register_host_after_delay(client, cluster, node_role, delay):
    aws_nodes = node_role["nodes"]
    for aws_node in aws_nodes:
        docker_run_cmd = \
            get_custom_host_registration_cmd(
                client, cluster, node_role["roles"], aws_node)
        aws_node.execute_command(docker_run_cmd)
        time.sleep(delay)
