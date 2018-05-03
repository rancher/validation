import random
import time
import inspect
import os
import cattle
import subprocess
import json

DEFAULT_TIMEOUT=120
CATTLE_TEST_URL = os.environ.get('CATTLE_TEST_URL', "http://localhost:80")
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', "None")

CATTLE_API_URL = CATTLE_TEST_URL +"/v3"

CATTLE_AUTH_URL = CATTLE_TEST_URL + "/v3-public/localproviders/local?action=login"
kube_fname = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          "k8s_kube_config")

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
    return "test" + "-" + str(random_int(10000,99999))


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
    #ns = wait_state(client, ns, "state", "active")
    time.sleep(3)
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
    crtb = client.update(crtb,
        roleTemplateId=role_template_id,
        userId=user.id)
    return crtb


def change_member_role_in_project(client, user, prtb, role_template_id):
    prtb = client.update(prtb,
        roleTemplateId=role_template_id,
        userId=user.id)
    return prtb


def create_kubeconfig(cluster):
    generateKubeConfigOutput = cluster.generateKubeconfig()
    print generateKubeConfigOutput.config
    file = open(kube_fname, "w")
    file.write(generateKubeConfigOutput.config)
    file.close()


def validate_workload(p_client, workload, type, ns_name, pod_count=1, wait_for_cron_pods=60):
    workload = wait_for_wl_to_active(p_client, workload)
    assert workload.state == "active"
    #For cronjob, wait for the first pod to get created after scheduled wait time
    if type == "cronJob":
        time.sleep(wait_for_cron_pods)
    pods = p_client.list_pod(workloadId=workload.id)
    assert len(pods) == pod_count
    for pod in pods:
        wait_for_pod_to_running(p_client,pod)
    wl_result = execute_kubectl_cmd("get " + type + " " + workload.name + " -n " +ns_name)
    if type == "deployment" or type == "statefulSet":
        assert wl_result["status"]["readyReplicas"] == pod_count
    if type == "daemonSet":
        assert wl_result["status"]["currentNumberScheduled"] == pod_count
    if type == "cronJob":
        assert len(wl_result["status"]["active"]) >= pod_count
        return
    for key, value in workload.workloadLabels.iteritems():
        label = key+"="+value
    get_pods = "get pods -l"+ label + " -n " + ns_name
    pods_result = execute_kubectl_cmd(get_pods)
    assert len(pods_result["items"]) == pod_count
    for pod in pods_result["items"]:
        assert pod["status"]["phase"] == "Running"


def validate_workload_with_sidekicks(p_client, workload, type , ns_name, pod_count=1):
    workload = wait_for_wl_to_active(p_client, workload)
    assert workload.state == "active"
    pods = p_client.list_pod(workloadId=workload.id)
    assert len(pods) == pod_count
    for pod in pods:
        wait_for_pod_to_running(p_client,pod)
    wl_result = execute_kubectl_cmd("get " + type + " " + workload.name + " -n " +ns_name)
    assert wl_result["status"]["readyReplicas"] == pod_count
    for key, value in workload.workloadLabels.iteritems():
        label = key+"="+value
    get_pods = "get pods -l"+ label + " -n " + ns_name
    wl_pods = execute_kubectl_cmd(get_pods)
    pods_result = execute_kubectl_cmd(get_pods)
    assert len(pods_result["items"]) == pod_count
    for pod in pods_result["items"]:
        assert pod["status"]["phase"] == "Running"
        assert len(pod["status"]["containerStatuses"]) == 2
        assert "running" in pod["status"]["containerStatuses"][0]["state"]
        assert "running" in pod["status"]["containerStatuses"][1]["state"]


def execute_kubectl_cmd(cmd, json_out=True):
    command = 'kubectl --kubeconfig {0} {1}'.format(
        kube_fname, cmd)
    if json_out:
        command += ' -o json'
    result = run_command(command)
    if json_out:
        result = json.loads(result)
    print result
    return result


def run_command(command):
    output = subprocess.check_output(command, shell=True)
    return output


def wait_for_wl_to_active(client, workload, timeout=DEFAULT_TIMEOUT):
    start = time.time()
    workloads = client.list_workload(uuid=workload.uuid)
    assert len(workloads) == 1
    wl = workloads[0]
    while wl.state != "active":
        if time.time() - start > timeout:
            raise AssertionError("Timed out waiting for state to get to active")
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
            raise AssertionError("Timed out waiting for state to get to active")
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
    etcd_nodes =[]
    control_nodes =[]
    worker_nodes =[]
    node_list =[]
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


def validate_ingress(p_client, cluster, workload, host, path):
    time.sleep(30)
    nodes = get_schedulable_nodes(cluster)
    pods = p_client.list_pod(workloadId=workload.id)
    target_name_list=[]
    for pod in pods:
        target_name_list.append(pod.name.encode('UTF-8'))
    for node in nodes:
        target_hit_list = target_name_list[:]
        host_ip = node.externalIpAddress
        for i in range(1,20):
            if len(target_hit_list) == 0:
                break
            cmd = "curl --header 'Host: "+host+"' http://"+host_ip+path
            print cmd
            result = run_command(cmd)
            result = result.rstrip()
            print result
            assert result in target_name_list
            if result in target_hit_list:
                target_hit_list.remove(result)
        assert len(target_hit_list) == 0