import random
import time
import inspect
import os
import cattle
import subprocess
import json
import paramiko


DEFAULT_TIMEOUT = 120
CATTLE_TEST_URL = os.environ.get('CATTLE_TEST_URL', "http://localhost:80")
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', "None")

CATTLE_API_URL = CATTLE_TEST_URL + "/v3"

CATTLE_AUTH_URL = \
    CATTLE_TEST_URL + "/v3-public/localproviders/local?action=login"
kube_fname = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          "k8s_kube_config")
MACHINE_TIMEOUT = os.environ.get('MACHINE_TIMEOUT', "1200")

TEST_CLIENT_IMAGE = "sangeetha/testclient"
TEST_TARGET_IMAGE = "sangeetha/testnewhostrouting"


def random_str():
    return 'random-{0}-{1}'.format(random_num(), int(time.time()))


def random_num():
    return random.randint(0, 1000000)


def random_int(start, end):
    return random.randint(start, end)


def random_test_name(name="test"):
    return name+"-"+str(random_int(10000, 99999))


def get_admin_client():
    return cattle.Client(url=CATTLE_API_URL, token=ADMIN_TOKEN, verify=False)


def get_client_for_token(token):
    return cattle.Client(url=CATTLE_API_URL, token=token, verify=False)


def get_project_client_for_token(project, token):
    p_url = project.links['self'] + '/schemas'
    p_client = cattle.Client(url=p_url, token=token, verify=False)
    return p_client


def get_cluster_client_for_token(cluster, token):
    c_url = cluster.links['self'] + '/schemas'
    c_client = cattle.Client(url=c_url, token=token, verify=False)
    return c_client


def up(cluster, token):
    c_url = cluster.links['self'] + '/schemas'
    c_client = cattle.Client(url=c_url, token=token, verify=False)
    return c_client


def wait_state(client, obj, state, timeout=DEFAULT_TIMEOUT):
    wait_for(lambda: client.reload(obj).state == state, timeout)
    return client.reload(obj)


def wait_for_condition(client, resource, check_function, fail_handler=None,
                       timeout=DEFAULT_TIMEOUT):
    start = time.time()
    resource = client.reload(resource)
    while not check_function(resource):
        if time.time() - start > timeout:
            exceptionMsg = 'Timeout waiting for ' + resource.baseType + \
                ' to satisfy condition: ' + \
                inspect.getsource(check_function)
            if (fail_handler):
                exceptionMsg = exceptionMsg + fail_handler(resource)
            raise Exception(exceptionMsg)

        time.sleep(.5)
        resource = client.reload(resource)

    return resource


def wait_for(callback, timeout=DEFAULT_TIMEOUT, timeout_message=None):
    start = time.time()
    ret = callback()
    while ret is None or ret is False:
        time.sleep(.5)
        if time.time() - start > timeout:
            if timeout_message:
                raise Exception(timeout_message)
            else:
                raise Exception('Timeout waiting for condition')
        ret = callback()
    return ret


def random_name():
    return "test" + "-" + str(random_int(10000, 99999))


def create_project_and_ns(token, cluster):
    client = get_client_for_token(token)
    p = create_project(client, cluster)
    c_client = get_cluster_client_for_token(cluster, token)
    ns = create_ns(c_client, cluster, p)
    return p, ns


def create_project(client, cluster):
    p = client.create_project(name=random_name(),
                              clusterId=cluster.id)
    p = client.wait_success(p)
    assert p.state == 'active'
    return p


def create_ns(client, cluster, project):
    ns = client.create_namespace(name=random_name(),
                                 clusterId=cluster.id,
                                 projectId=project.id)
    # ns = wait_state(client, ns, "state", "active")
    wait_for_ns_to_become_active(client, ns)
    ns = client.reload(ns)
    assert ns.state == 'active'
    return ns


def assign_members_to_cluster(client, user, cluster, role_template_id):
    crtb = client.create_cluster_role_template_binding(
        clusterId=cluster.id,
        roleTemplateId=role_template_id,
        subjectKind="User",
        userId=user.id)
    return crtb


def assign_members_to_project(client, user, project, role_template_id):
    prtb = client.create_project_role_template_binding(
        projectId=project.id,
        roleTemplateId=role_template_id,
        subjectKind="User",
        userId=user.id)
    return prtb


def change_member_role_in_cluster(client, user, crtb, role_template_id):
    crtb = client.update(
        crtb,
        roleTemplateId=role_template_id,
        userId=user.id)
    return crtb


def change_member_role_in_project(client, user, prtb, role_template_id):
    prtb = client.update(
        prtb,
        roleTemplateId=role_template_id,
        userId=user.id)
    return prtb


def create_kubeconfig(cluster):
    generateKubeConfigOutput = cluster.generateKubeconfig()
    print generateKubeConfigOutput.config
    file = open(kube_fname, "w")
    file.write(generateKubeConfigOutput.config)
    file.close()


def validate_workload(p_client, workload, type, ns_name, pod_count=1,
                      wait_for_cron_pods=60):
    workload = wait_for_wl_to_active(p_client, workload)
    assert workload.state == "active"
    # For cronjob, wait for the first pod to get created after
    # scheduled wait time
    if type == "cronJob":
        time.sleep(wait_for_cron_pods)
    pods = p_client.list_pod(workloadId=workload.id)
    assert len(pods) == pod_count
    for pod in pods:
        wait_for_pod_to_running(p_client, pod)
    wl_result = execute_kubectl_cmd(
        "get " + type + " " + workload.name + " -n " + ns_name)
    if type == "deployment" or type == "statefulSet":
        assert wl_result["status"]["readyReplicas"] == pod_count
    if type == "daemonSet":
        assert wl_result["status"]["currentNumberScheduled"] == pod_count
    if type == "cronJob":
        assert len(wl_result["status"]["active"]) >= pod_count
        return
    for key, value in workload.workloadLabels.iteritems():
        label = key+"="+value
    get_pods = "get pods -l" + label + " -n " + ns_name
    pods_result = execute_kubectl_cmd(get_pods)
    assert len(pods_result["items"]) == pod_count
    for pod in pods_result["items"]:
        assert pod["status"]["phase"] == "Running"
    return pods_result["items"]


def validate_workload_with_sidekicks(p_client, workload, type, ns_name,
                                     pod_count=1):
    workload = wait_for_wl_to_active(p_client, workload)
    assert workload.state == "active"
    pods = wait_for_pods_in_workload(p_client, workload, pod_count)
    assert len(pods) == pod_count
    for pod in pods:
        wait_for_pod_to_running(p_client, pod)
    wl_result = execute_kubectl_cmd(
        "get " + type + " " + workload.name + " -n " + ns_name)
    assert wl_result["status"]["readyReplicas"] == pod_count
    for key, value in workload.workloadLabels.iteritems():
        label = key+"="+value
    get_pods = "get pods -l" + label + " -n " + ns_name
    execute_kubectl_cmd(get_pods)
    pods_result = execute_kubectl_cmd(get_pods)
    assert len(pods_result["items"]) == pod_count
    for pod in pods_result["items"]:
        assert pod["status"]["phase"] == "Running"
        assert len(pod["status"]["containerStatuses"]) == 2
        assert "running" in pod["status"]["containerStatuses"][0]["state"]
        assert "running" in pod["status"]["containerStatuses"][1]["state"]


def execute_kubectl_cmd(cmd, json_out=True, stderr=False):
    command = 'kubectl --kubeconfig {0} {1}'.format(
        kube_fname, cmd)
    if json_out:
        command += ' -o json'
    if stderr:
        result = run_command_with_stderr(command)
    else:
        result = run_command(command)
    if json_out:
        result = json.loads(result)
    print result
    return result


def run_command(command):
    return subprocess.check_output(command, shell=True)


def run_command_with_stderr(command):
    try:
        output = subprocess.check_output(command, shell=True,
                                         stderr=subprocess.STDOUT)
        returncode = 0
    except subprocess.CalledProcessError as e:
        output = e.output
        returncode = e.returncode
    print(returncode)
    return output


def wait_for_wl_to_active(client, workload, timeout=DEFAULT_TIMEOUT):
    start = time.time()
    workloads = client.list_workload(uuid=workload.uuid)
    assert len(workloads) == 1
    wl = workloads[0]
    while wl.state != "active":
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for state to get to active")
        time.sleep(.5)
        workloads = client.list_workload(uuid=workload.uuid)
        assert len(workloads) == 1
        wl = workloads[0]
    return wl


def wait_for_pod_to_running(client, pod, timeout=DEFAULT_TIMEOUT):
    start = time.time()
    pods = client.list_pod(uuid=pod.uuid)
    assert len(pods) == 1
    p = pods[0]
    while p.state != "running":
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for state to get to active")
        time.sleep(.5)
        pods = client.list_pod(uuid=pod.uuid)
        assert len(pods) == 1
        p = pods[0]
    return p


def get_schedulable_nodes(cluster):
    client = get_admin_client()
    nodes = client.list_node(clusterId=cluster.id)
    schedulable_nodes = []
    for node in nodes:
        if node.controlPlane or node.worker:
            schedulable_nodes.append(node)
    return schedulable_nodes


def get_role_nodes(cluster, role):
    etcd_nodes = []
    control_nodes = []
    worker_nodes = []
    node_list = []
    client = get_admin_client()
    nodes = client.list_node(clusterId=cluster.id)
    for node in nodes:
        if node.etcd:
            etcd_nodes.append(node)
        if node.controlPlane:
            control_nodes.append(node)
        if node.worker:
            worker_nodes.append(node)
    if role == "etcd":
        node_list = etcd_nodes
    if role == "control":
        node_list = control_nodes
    if role == "worker":
        node_list = worker_nodes
    return node_list


def validate_ingress(p_client, cluster, workloads, host, path,
                     insecure_redirect=False):
    time.sleep(10)
    curl_cmd = "curl "
    if (insecure_redirect):
        curl_cmd = "curl -L --insecure "
    if len(host) > 0:
        curl_cmd += " --header 'Host: "+host+"'"
    nodes = get_schedulable_nodes(cluster)
    pods = []
    for workload in workloads:
        pod_list = p_client.list_pod(workloadId=workload.id)
        pods.extend(pod_list)
    target_name_list = []
    for pod in pods:
        target_name_list.append(pod.name)
    print "target name list:" + str(target_name_list)
    for node in nodes:
        target_hit_list = target_name_list[:]
        host_ip = node.externalIpAddress
        for i in range(1, 20):
            if len(target_hit_list) == 0:
                break
            cmd = curl_cmd + " http://"+host_ip+path
            print cmd
            result = run_command(cmd)
            result = result.rstrip()
            print result
            assert result in target_name_list
            if result in target_hit_list:
                target_hit_list.remove(result)
        assert len(target_hit_list) == 0


def validate_ingress_using_endpoint(p_client, ingress, workloads,
                                    timeout=300):
    pods = []
    for workload in workloads:
        pod_list = p_client.list_pod(workloadId=workload.id)
        pods.extend(pod_list)
    target_name_list = []
    for pod in pods:
        target_name_list.append(pod.name)
    print "target name list:" + str(target_name_list)
    start = time.time()
    fqdn_available = False
    url = None
    while not fqdn_available:
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for state to get to active")
        time.sleep(.5)
        ingress_list = p_client.list_ingress(uuid=ingress.uuid)
        assert len(ingress_list) == 1
        ingress = ingress_list[0]
        for public_endpoint in ingress.publicEndpoints:
            if public_endpoint["hostname"].startswith(ingress.name):
                fqdn_available = True
                url = \
                    public_endpoint["protocol"].lower() + "://" + \
                    public_endpoint["hostname"]
                if "path" in public_endpoint.keys():
                    url += public_endpoint["path"]
    time.sleep(5)
    target_hit_list = target_name_list[:]
    for i in range(1, 20):
        if len(target_hit_list) == 0:
            break
        cmd = "curl " + url
        print cmd
        result = run_command(cmd)
        result = result.rstrip()
        print result
        assert result in target_name_list
        if result in target_hit_list:
            target_hit_list.remove(result)
    assert len(target_hit_list) == 0


def validate_cluster(client, cluster, intermediate_state="provisioning",
                     check_intermediate_state=True, skipIngresscheck=False,
                     nodes_not_in_active_state=[]):
    if check_intermediate_state:
        cluster = wait_for_condition(
            client, cluster,
            lambda x: x.state == intermediate_state,
            lambda x: 'State is: ' + x.state,
            timeout=MACHINE_TIMEOUT)
        assert cluster.state == intermediate_state
    cluster = wait_for_condition(
        client, cluster,
        lambda x: x.state == "active",
        lambda x: 'State is: ' + x.state,
        timeout=MACHINE_TIMEOUT)
    assert cluster.state == "active"
    wait_for_nodes_to_become_active(client, cluster,
                                    exception_list=nodes_not_in_active_state)
    # Create Daemon set workload and have an Ingress with Workload
    # rule pointing to this daemonset
    create_kubeconfig(cluster)
    project, ns = create_project_and_ns(ADMIN_TOKEN, cluster)
    p_client = get_project_client_for_token(project, ADMIN_TOKEN)
    con = [{"name": "test1",
           "image": "sangeetha/testnewhostrouting"}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        daemonSetConfig={})
    validate_workload(p_client, workload, "daemonSet", ns.name,
                      len(get_schedulable_nodes(cluster)))
    host = "test"+str(random_int(10000, 99999))+".com"
    path = "/name.html"
    rule = {"host": host,
            "paths":
                {path: {"workloadIds": [workload.id], "targetPort": "80"}}}
    p_client.create_ingress(name=name,
                            namespaceId=ns.id,
                            rules=[rule])
    if not skipIngresscheck:
        validate_ingress(p_client, cluster, [workload], host, path)
    return cluster


def validate_dns_record(pod, record, expected):
    #requires pod with `dig` available (sangeetha/testclient)
    host = '{0}.{1}.svc.cluster.local'.format(
        record["name"], record["namespaceId"])

    cmd = 'ping -c 1 -W 1 {0}'.format(host)
    output = kubectl_pod_exec(pod, cmd)
    assert "0% packet loss" in str(output)

    dig_cmd = 'dig {0} +short'.format(host)
    output = kubectl_pod_exec(pod, dig_cmd)

    for expected_value in expected:
        assert expected_value in str(output)


def wait_for_nodes_to_become_active(client, cluster, exception_list=[]):
    nodes = client.list_node(clusterId=cluster.id)
    for node in nodes:
        if node.requestedHostname not in exception_list:
            wait_for_node_status(client, node, "active")


def wait_for_node_status(client, node, state):
    node = wait_for_condition(
        client, node,
        lambda x: x.state == state,
        lambda x: 'State is: ' + x.state,
        timeout=MACHINE_TIMEOUT)
    return node


def wait_for_node_to_be_deleted(client, node, timeout=300):
    uuid = node.uuid
    start = time.time()
    nodes = client.list_node(uuid=uuid)
    node_count = len(nodes)
    while node_count != 0:
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for state to get to active")
        time.sleep(.5)
        nodes = client.list_node(uuid=uuid)
        node_count = len(nodes)


def wait_for_cluster_node_count(client, cluster, expected_node_count,
                                timeout=300):
    start = time.time()
    nodes = client.list_node(clusterId=cluster.id)
    node_count = len(nodes)
    while node_count != expected_node_count:
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for state to get to active")
        time.sleep(.5)
        nodes = client.list_node(clusterId=cluster.id)
        node_count = len(nodes)


def get_custom_host_registration_cmd(client, cluster, roles, node):
    allowed_roles = ["etcd", "worker", "controlplane"]
    cluster_tokens = client.list_cluster_registration_token(
        clusterId=cluster.id)
    if len(cluster_tokens) > 0:
        cluster_token = cluster_tokens[0]
    else:
        cluster_token = create_custom_host_registration_token(client, cluster)
    cmd = cluster_token.nodeCommand
    for role in roles:
        assert role in allowed_roles
        cmd += " --"+role
    additional_options = " --address " + node.public_ip_address + \
                         " --internal-address " + node.private_ip_address
    cmd += additional_options
    return cmd


def create_custom_host_registration_token(client, cluster):
    cluster_token = client.create_cluster_registration_token(
        clusterId=cluster.id)
    cluster_token = client.wait_success(cluster_token)
    assert cluster_token.state == 'active'
    return cluster_token


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


def check_connectivity_between_workloads(p_client1, workload1, p_client2,
                                         workload2,
                                         password, allow_connectivity=True):
    wl1_pods = p_client1.list_pod(workloadId=workload1.id)
    wl2_pods = p_client2.list_pod(workloadId=workload2.id)
    for pod in wl1_pods:
        for o_pod in wl2_pods:
            check_connectivity_between_pods(pod, o_pod, password)


def check_connectivity_between_workload_pods(p_client, workload, password):
    pods = p_client.list_pod(workloadId=workload.id)
    for pod in pods:
        for o_pod in pods:
            check_connectivity_between_pods(pod, o_pod, password)


def check_connectivity_between_pods(pod1, pod2, password,
                                    allow_connectivity=True):
    pod_ip = pod2.status.podIp

    cmd = "ping -c 1 -W 1 " + pod_ip
    response = kubectl_pod_exec(pod1, cmd)
    print "Actual ping Response" + str(response)
    if allow_connectivity:
        assert pod_ip in str(response) and "0% packet loss" in str(response)
    else:
        assert pod_ip in str(response) and "100% packet loss" in str(response)


def kubectl_pod_exec(pod, cmd):
    command = "exec " + pod.name + " -n " + pod.namespaceId + " -- " + cmd
    return execute_kubectl_cmd(command, json_out=False, stderr=True)


def exec_shell_command(ip, port, cmd, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username="root", password=password, port=port)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    response = stdout.readlines()
    return response


def wait_for_ns_to_become_active(client, ns, timeout=DEFAULT_TIMEOUT):
    start = time.time()
    time.sleep(2)
    nss = client.list_namespace(uuid=ns.uuid)
    assert len(nss) == 1
    ns = nss[0]
    while ns.state != "active":
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for state to get to active")
        time.sleep(.5)
        nss = client.list_namespace(uuid=ns.uuid)
        assert len(nss) == 1
        ns = nss[0]
    return ns


def wait_for_pods_in_workload(p_client, workload, pod_count,
                              timeout=DEFAULT_TIMEOUT):
    start = time.time()
    pods = p_client.list_pod(workloadId=workload.id)
    while len(pods) != pod_count:
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for state to get to active")
        time.sleep(.5)
        pods = p_client.list_pod(workloadId=workload.id)
    return pods


def get_admin_client_and_cluster():
    client = get_admin_client()
    clusters = client.list_cluster()
    assert len(clusters) > 0
    cluster = clusters[0]
    return client, cluster
