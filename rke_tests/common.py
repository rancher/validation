def create_and_validate_rke_cluster(test_name, cloud_provider, rke_client,
                                    kubectl, rke_template, number_of_nodes):
    """
    General rke up test validation
    Provision 'number of nodes'
    Generate rke YAML from template, and marks each node with roles
    Calls rke up, and runs validations methods for:
        node roles validation
        intercommuincation per pod
        dns service discovery validation
    """

    node_name = '{}-node'.format(test_name)

    # create node from cloud provider
    nodes = cloud_provider.create_multiple_nodes(
        number_of_nodes, node_name, wait_for_ready=True)

    try:
        # create rke cluster yml
        config_yml, nodes = rke_client.build_rke_template(rke_template, nodes)

        # run rke up
        result = rke_client.up(config_yml)
        assert result.ok, result.stderr

        # validate k8s reachable
        kubectl.kube_config_path = rke_client.kube_config_path()
        validation_node_roles(nodes, kubectl.get_nodes())
        validate_private_ip_intercommunication(kubectl)
        validate_dns_service_discovery(kubectl)
    finally:
        for node in nodes:
            cloud_provider.delete_node(node)


def match_nodes(nodes, k8s_nodes):
    """
    Builds a list of tuples, where:
    nodes_to_k8s_nodes[0][0] is the node object matched to
    nodes_to_k8s_nodes[0][1] is the k8s info for the same node
    TODO: what about etcd only nodes? are they returned in kubectl get nodes?
    """

    nodes_to_k8s_nodes = []
    for k8s_node in k8s_nodes['items']:
        hostname = k8s_node['metadata']['labels']['kubernetes.io/hostname']
        for node in nodes:
            if hostname == node.public_ip_address or \
                    hostname == node.host_name:
                nodes_to_k8s_nodes.append((node, k8s_node))
    return nodes_to_k8s_nodes


def assert_containers_exist_for_role(role, containers, expect_containers):
    missing_containers = expect_containers[:]
    for container in containers:
        if container in expect_containers:
            missing_containers.remove(container)
    assert len(missing_containers) == 0, \
        "Missing expected containers for role '{0}': {1}".format(
            role, missing_containers)


def validation_node_roles(nodes, k8s_nodes):
    """
    Validates each node's labels for match its roles
    Validates each node's running containers match its role
    Validates etcd etcdctl cluster-health command
    Validates worker nodes nginx-proxy conf file for controlplane ips
    """
    # TODO: etcd only nodes are not listed in k8s_nodes, should handle this
    # TODO: does hostname_override affect nginx-proxy controlplane ips?

    role_matcher = {
        'worker': 'node-role.kubernetes.io/worker',
        'etcd': 'node-role.kubernetes.io/etcd',
        'controlplane': 'node-role.kubernetes.io/master'}
    controlplane = [
        'scheduler', 'kube-controller', 'kubelet', 'kube-proxy', 'kube-api']
    worker = ['kubelet', 'kube-proxy', 'nginx-proxy']
    etcd = ['etcd']

    controlplane_ips = []
    for node in nodes:
        if 'controlplane' in node.roles:
            controlplane_ips.append(node.public_ip_address)

    nodes_to_k8s_nodes = match_nodes(nodes, k8s_nodes)
    for node, k8s_node in nodes_to_k8s_nodes:
        for role in node.roles:
            assert role_matcher[role] in k8s_node['metadata']['labels'].keys()
            containers = node.docker_ps().keys()
            if role == 'controlplane':
                assert_containers_exist_for_role(
                    role, containers, controlplane)
            # nodes with work and controlplane roles do not have nginx-proxy
            if role == 'worker' and 'controlplane' not in node.roles:
                assert_containers_exist_for_role(role, containers, worker)
                result = node.docker_exec(
                    'nginx-proxy', 'cat /etc/nginx/nginx.conf')
                for ip in controlplane_ips:
                    assert 'server {0}:6443'.format(ip) in result, result
            if role == 'etcd':
                assert_containers_exist_for_role(role, containers, etcd)
                result = node.docker_exec('etcd', 'etcdctl cluster-health')
                assert 'cluster is healthy' in result


def validate_private_ip_intercommunication(kubectl):
    """
    Creates a daemonset of pods, one pod per worker node
    Gets pod name, pod ip, host ip, and containers
    For each pod, use kubectl exec to ping all other pod ips
    Asserts that each ping is successful
    Tears down daemonset
    """

    namespace = 'default'
    yml_file = 'resources/k8s_ymls/daemonset_test1.yaml'

    # create pod on each worker node
    result = kubectl.create_resourse_from_yml(yml_file, namespace=namespace)
    assert result.ok, result.stderr

    kubectl.wait_for_pods(
        selector='name=daemonset-test1', namespace=namespace)
    # get pods on each node/namespaces to test intercommunication with pods on
    # different nodes
    pods = kubectl.get_resource(
        'pods', namespace=namespace, selector='name=daemonset-test1')
    pod_list = {}
    for pod in pods['items']:
        pod_name = pod['metadata']['name']
        pod_list[pod_name] = {
            'pod_ip': pod['status']['podIP'],
            'host_ip': pod['status']['hostIP'],
            'containers': [x['name'] for x in pod['spec']['containers']]}

    for pod_name in pod_list.keys():
        for pod, pod_info in pod_list.iteritems():
            if pod_name == pod:
                continue  # Skip pinging self
            cmd = 'ping -c 1 {0}'.format(pod_info['pod_ip'])
            result = kubectl.exec_cmd(pod_name, cmd, namespace)
            expect_result = '1 packets transmitted, 1 received, 0% packet loss'
            assert expect_result in result.stdout

    result = kubectl.delete_resourse_from_yml(yml_file, namespace=namespace)


def validate_dns_service_discovery(kubectl):
    """
    Creates two namespaces
    Creates a service in each namespace, gets service IP
    Creates a single pod in first namespace
    With pod, service dns record,
    kubectl exec dig dns_record +short and assert that service IP
    """

    namespace_one = 'nsone'
    namespace_two = 'nstwo'
    services = {
        'k8test1': {
            'namespace': namespace_one,
            'yml_file': 'resources/k8s_ymls/service1_ingress.yml',
        },
        'k8test2': {
            'namespace': namespace_two,
            'yml_file': 'resources/k8s_ymls/service2_ingress.yml',
        }
    }

    kubectl.create_ns(namespace_one)
    kubectl.create_ns(namespace_two)

    dns_records = {}
    for service_name, service_info in services.iteritems():
        namespace = service_info['namespace']
        # create service
        result = kubectl.create_resourse_from_yml(
            service_info['yml_file'], namespace=namespace)
        assert result.ok, result.stderr
        # map expected IP to dns service name
        dns = "{0}.{1}.svc.cluster.local".format(service_name, namespace)
        svc = kubectl.get_resource(
            'svc', resource_name=service_name, namespace=namespace)
        dns_records.update({dns: svc["spec"]["clusterIP"]})

    result = kubectl.create_resourse_from_yml(
        'resources/k8s_ymls/single_pod.yml', namespace=namespace_one)
    assert result.ok, result.stderr
    kubectl.wait_for_pods(
        selector='k8s-app=pod-test-util', namespace=namespace)

    for dns_record, expected_ip in dns_records.iteritems():
        cmd = 'dig {0} +short'.format(dns_record)
        result = kubectl.exec_cmd('pod-test-util', cmd, namespace_one)
        assert expected_ip in result.stdout, (
            "Unable to test DNS resolution for service {0}: {1}".format(
                dns_record, result.stderr))

    kubectl.delete_resourse('pod', 'pod-test-util', namespace=namespace_one)

    for service_name, service_info in services.iteritems():
        kubectl.delete_resourse_from_yml(
            service_info['yml_file'], namespace=service_info['namespace'])
        kubectl.delete_resourse('namespace', service_info['namespace'])


def validate_dashboard(kubectl):
    # Start dashboard
    # Validated it is reachable
    pass
