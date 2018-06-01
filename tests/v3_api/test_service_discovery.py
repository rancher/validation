from common import *  # NOQA
import pytest

CLUSTER_NAME = os.environ.get("CLUSTER_NAME", "")
RANCHER_CLEANUP_PROJECT = os.environ.get("RANCHER_CLEANUP_PROJECT", "True")
namespace = {"p_client": None, "ns": None, "cluster": None,
             "project": None, "testclient_pods": [], "workload": None}


def test_dns_record_type_external_ip():
    ns = namespace["ns"]
    record = {"type": "dnsRecord", "ipAddresses": ["8.8.8.8"],
              "name": random_test_name("record"), "namespaceId": ns.id}
    expected = record["ipAddresses"]
    create_and_validate_dns_record(record, expected)


def test_dns_record_type_multiple_external_ips():
    ns = namespace["ns"]
    record = {"type": "dnsRecord", "ipAddresses": ["8.8.8.8", "4.4.4.4"],
              "name": random_test_name("record"), "namespaceId": ns.id}
    expected = record["ipAddresses"]
    create_and_validate_dns_record(record, expected)


def test_dns_record_type_hostname():
    ns = namespace["ns"]
    record = {"type": "dnsRecord", "hostname": "google.com",
              "name": random_test_name("record"), "namespaceId": ns.id}
    expected = [record["hostname"]]
    create_and_validate_dns_record(record, expected)


def test_dns_record_type_alias():
    ns = namespace["ns"]

    first_record = {"type": "dnsRecord", "hostname": "google.com",
                    "name": random_test_name("record"), "namespaceId": ns.id}
    target_record = create_dns_record(first_record)

    record = {"type": "dnsRecord", "targetDnsRecordIds": [target_record["id"]],
              "name": random_test_name("record"), "namespaceId": ns.id}

    expected = [first_record["hostname"]]
    create_and_validate_dns_record(record, expected)


def test_dns_record_type_workload():
    ns = namespace["ns"]
    workload = namespace["workload"]
    p_client = namespace["p_client"]

    record = {"type": "dnsRecord", "targetWorkloadIds": [workload["id"]],
              "name": random_test_name("record"), "namespaceId": ns.id}

    expected_ips = []
    pods = p_client.list_pod(workloadId=workload["id"])
    for pod in pods:
        expected_ips.append(pod["status"]["podIp"])

    create_and_validate_dns_record(record, expected_ips)


def test_dns_record_type_multiple_workloads():
    ns = namespace["ns"]
    workload = namespace["workload"]
    p_client = namespace["p_client"]

    wlname = random_test_name("default")

    con = [{"name": "test1",
            "image": TEST_TARGET_IMAGE}]

    additional_workload = p_client.create_workload(name=wlname,
                                                   containers=con,
                                                   namespaceId=ns.id,
                                                   scale=1)
    wait_for_wl_to_active(p_client, additional_workload)
    awl_pods = wait_for_pods_in_workload(p_client, additional_workload, 1)
    wait_for_pod_to_running(p_client, awl_pods[0])

    record = {"type": "dnsRecord",
              "targetWorkloadIds": [workload["id"], additional_workload["id"]],
              "name": random_test_name("record"),
              "namespaceId": ns.id}

    workloads = [workload, additional_workload]
    expected_ips = []

    for wl in workloads:
        pods = p_client.list_pod(workloadId=wl["id"])
        for pod in pods:
            expected_ips.append(pod["status"]["podIp"])

    create_and_validate_dns_record(record, expected_ips)


def test_dns_record_type_selector():
    ns = namespace["ns"]
    workload = namespace["workload"]
    p_client = namespace["p_client"]

    selector = \
        workload["labels"]["workload.user.cattle.io/workloadselector"]

    record = {"type": "dnsRecord",
              "selector":
                  {"workload.user.cattle.io/workloadselector": selector},
              "name": random_test_name("record"), "namespaceId": ns.id}

    expected_ips = []
    pods = p_client.list_pod(workloadId=workload["id"])
    for pod in pods:
        expected_ips.append(pod["status"]["podIp"])

    create_and_validate_dns_record(record, expected_ips)


def create_and_validate_dns_record(record, expected):
    testclient_pods = namespace["testclient_pods"]
    create_dns_record(record)
    for pod in testclient_pods:
        validate_dns_record(pod, record, expected)


def create_dns_record(record):
    p_client = namespace["p_client"]
    created_record = p_client.create_dns_record(record)

    wait_for_condition(
        p_client, created_record,
        lambda x: x.state == "active",
        lambda x: 'State is: ' + x.state)

    return created_record


@pytest.fixture(scope='module', autouse="True")
def setup(request):
    client = get_admin_client()

    if CLUSTER_NAME == "":
        clusters = client.list_cluster()
    else:
        clusters = client.list_cluster(name=CLUSTER_NAME)
    assert len(clusters) >= 1

    cluster = clusters[0]
    create_kubeconfig(cluster)

    p, ns = create_project_and_ns(ADMIN_TOKEN, cluster)
    p_client = get_project_client_for_token(p, ADMIN_TOKEN)
    c_client = get_cluster_client_for_token(cluster, ADMIN_TOKEN)

    new_ns = create_ns(c_client, cluster, p)

    namespace["p_client"] = p_client
    namespace["ns"] = ns
    namespace["cluster"] = cluster
    namespace["project"] = p

    wlname = random_test_name("default")

    con = [{"name": "test1",
            "image": TEST_CLIENT_IMAGE}]

    workload = p_client.create_workload(name=wlname,
                                        containers=con,
                                        namespaceId=ns.id,
                                        scale=2)
    wait_for_wl_to_active(p_client, workload)
    namespace["workload"] = workload

    pods = wait_for_pods_in_workload(p_client, workload, 2)
    pod = wait_for_pod_to_running(p_client, pods[0])
    namespace["testclient_pods"].append(pod)

    workload = p_client.create_workload(name=wlname,
                                        containers=con,
                                        namespaceId=new_ns.id,
                                        scale=1)
    wait_for_wl_to_active(p_client, workload)
    pods = wait_for_pods_in_workload(p_client, workload, 1)
    pod = wait_for_pod_to_running(p_client, pods[0])
    namespace["testclient_pods"].append(pod)

    assert len(namespace["testclient_pods"]) == 2

    def fin():
        client = get_admin_client()
        client.delete(namespace["project"])

    if RANCHER_CLEANUP_PROJECT == "True":
        request.addfinalizer(fin)
