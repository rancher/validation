import base64
import ast
import pytest

from .common import *  # NOQA
from .test_secrets import (
    create_and_validate_workload_with_secret_as_env_variable,
    create_and_validate_workload_with_secret_as_volume,
    create_secret)
from .test_service_discovery import create_dns_record

cluster_name = os.environ.get('RANCHER_CLUSTER_NAME', "")
validate_prefix = os.environ.get('RANCHER_VALIDATE_RESOURCES_PREFIX', "step0")
create_prefix = os.environ.get('RANCHER_CREATE_RESOURCES_PREFIX', "step1")
cluster_details = {}
namespace = {"p_client": None, "ns": None, "cluster": None, "project": None,
             "testclient_pods": []}
upgrade_check_stage = os.environ.get('RANCHER_UPGRADE_CHECK', "preupgrade")
validate_ingress = \
    ast.literal_eval(os.environ.get('RANCHER_INGRESS_CHECK', "True"))

wl_name = "-testwl"
sd_name = "-testsd"
sd_wlname1 = "-testsd1"
sd_wlname2 = "-testsd2"
ingress_name1 = "-testingress1"
ingress_name2 = "-testingress2"
ingress_wlname1 = "-testingresswl1"
ingress_wlname2 = "-testingresswl2"
project_name = "-p1"
ns_name1 = "-ns1"
ns_name2 = "-ns2"


wl_name_create = create_prefix + wl_name
sd_name_create = create_prefix + sd_name
sd_wlname1_create = create_prefix + sd_wlname1
sd_wlname2_create = create_prefix + sd_wlname2
ingress_name1_create = create_prefix + ingress_name1
ingress_name2_create = create_prefix + ingress_name2
ingress_wlname1_create = create_prefix + ingress_wlname1
ingress_wlname2_create = create_prefix + ingress_wlname2

wl_name_validate = validate_prefix + wl_name
sd_name_validate = validate_prefix + sd_name
sd_wlname1_validate = validate_prefix + sd_wlname1
sd_wlname2_validate = validate_prefix + sd_wlname2
ingress_name1_validate = validate_prefix + ingress_name1
ingress_name2_validate = validate_prefix + ingress_name2
ingress_wlname1_validate = validate_prefix + ingress_wlname1
ingress_wlname2_validate = validate_prefix + ingress_wlname2

if_post_upgrade = pytest.mark.skipif(
    upgrade_check_stage != "postupgrade",
    reason='This test is not executed for PreUpgrade checks')
if_pre_upgrade = pytest.mark.skipif(
    upgrade_check_stage != "preupgrade",
    reason='This test is not executed for PreUpgrade checks')


@if_pre_upgrade
def test_upgrade_create_and_validate_resources():
    create_and_validate_wl()
    create_and_validate_service_discovery()
    create_wokloads_with_secret()
    if validate_ingress:
        create_and_validate_ingress_xip_io()


@if_post_upgrade
def test_upgrade_validate_resources():
    # Validate existing resources
    validate_wl(wl_name_validate)
    validate_service_discovery(sd_name_validate,
                               [sd_wlname1_validate, sd_wlname2_validate])
    if validate_ingress:
        validate_ingress_xip_io(ingress_name1_validate,
                                ingress_wlname1_validate)
        validate_ingress_xip_io(ingress_name2_validate,
                                ingress_wlname2_validate)
    # Create and validate new resources
    create_project_resources()
    create_and_validate_wl()
    create_and_validate_service_discovery()
    create_wokloads_with_secret()
    if validate_ingress:
        create_and_validate_ingress_xip_io()


def create_and_validate_wl():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
            "image": TEST_TARGET_IMAGE}]
    p_client.create_workload(name=wl_name_create, containers=con,
                             namespaceId=ns.id, scale=2)
    validate_wl(wl_name_create)


def validate_wl(workload_name):
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    workloads = p_client.list_workload(name=workload_name,
                                       namespaceId=ns.id).data
    assert len(workloads) == 1
    workload = workloads[0]
    validate_workload(p_client, workload, "deployment", ns.name, pod_count=2)
    validate_service_discovery(workload_name, [workload_name])


def create_and_validate_ingress_xip_io():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    cluster = namespace["cluster"]
    con = [{"name": "test1",
            "image": TEST_TARGET_IMAGE}]

    # Ingress with daemonSet target
    workload = p_client.create_workload(name=ingress_wlname1_create,
                                        containers=con,
                                        namespaceId=ns.id,
                                        daemonSetConfig={})
    validate_workload(p_client, workload, "daemonSet", ns.name,
                      len(get_schedulable_nodes(cluster)))
    path = "/name.html"
    rule = {"host": "xip.io",
            "paths":
                {path: {"workloadIds": [workload.id], "targetPort": "80"}}}
    p_client.create_ingress(name=ingress_name1_create,
                            namespaceId=ns.id,
                            rules=[rule])
    validate_ingress_xip_io(ingress_name1_create, ingress_wlname1_create)

    # Ingress with Deployment target
    workload = p_client.create_workload(name=ingress_wlname2_create,
                                        containers=con,
                                        namespaceId=ns.id, scale=2)
    validate_wl(ingress_wlname2_create)
    path = "/name.html"
    rule = {"host": "xip.io",
            "paths":
                {path: {"workloadIds": [workload.id], "targetPort": "80"}}}
    p_client.create_ingress(name=ingress_name2_create,
                            namespaceId=ns.id,
                            rules=[rule])
    validate_ingress_xip_io(ingress_name2_create, ingress_wlname2_create)


def validate_ingress_xip_io(ing_name, workload_name):
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    workloads = p_client.list_workload(name=workload_name,
                                       namespaceId=ns.id).data
    assert len(workloads) == 1
    workload = workloads[0]
    ingresses = p_client.list_ingress(name=ing_name,
                                      namespaceId=ns.id).data
    assert len(ingresses) == 1
    ingress = ingresses[0]

    validate_ingress_using_endpoint(p_client, ingress, [workload])


def create_and_validate_service_discovery():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    cluster = namespace["cluster"]

    con = [{"name": "test1",
            "image": TEST_TARGET_IMAGE}]
    workload = p_client.create_workload(name=sd_wlname1_create,
                                        containers=con,
                                        namespaceId=ns.id,
                                        daemonSetConfig={})
    validate_workload(p_client, workload, "daemonSet", ns.name,
                      len(get_schedulable_nodes(cluster)))

    additional_workload = p_client.create_workload(name=sd_wlname2_create,
                                                   containers=con,
                                                   namespaceId=ns.id,
                                                   scale=1)
    wait_for_wl_to_active(p_client, additional_workload)
    awl_pods = wait_for_pods_in_workload(p_client, additional_workload, 1)
    wait_for_pod_to_running(p_client, awl_pods[0])

    record = {"type": "dnsRecord",
              "targetWorkloadIds": [workload["id"], additional_workload["id"]],
              "name": sd_name_create,
              "namespaceId": ns.id}

    create_dns_record(record, p_client)
    validate_service_discovery(sd_name_create,
                               [sd_wlname1_create, sd_wlname2_create])


def validate_service_discovery(sd_record_name, workload_names):
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    target_wls = []
    for wl_name_create in workload_names:
        workloads = p_client.list_workload(
            name=wl_name_create, namespaceId=ns.id).data
        assert len(workloads) == 1
        workload = workloads[0]
        target_wls.append(workload)

    records = p_client.list_dns_record(
        name=sd_record_name, namespaceId=ns.id).data
    assert len(records) == 1
    record = records[0]

    testclient_pods = namespace["testclient_pods"]
    expected_ips = []
    for wl in target_wls:
        pods = p_client.list_pod(workloadId=wl["id"]).data
        for pod in pods:
            expected_ips.append(pod["status"]["podIp"])

    assert len(testclient_pods) > 0
    for pod in testclient_pods:
        validate_dns_record(pod, record, expected_ips)


def create_wokloads_with_secret():
    value = base64.b64encode(b"valueall")
    keyvaluepair = {"testall": value.decode('utf-8')}

    p_client = namespace["p_client"]
    ns = namespace["ns"]

    secret_name = create_prefix + "-testsecret"
    wl_name_create1 = create_prefix + "-testwl1withsec"
    wl_name_create2 = create_prefix + "-testwl2withsec"

    secret = create_secret(keyvaluepair, p_client=p_client, name=secret_name)
    create_and_validate_workload_with_secret_as_volume(p_client,
                                                       secret,
                                                       ns,
                                                       keyvaluepair,
                                                       name=wl_name_create1)
    create_and_validate_workload_with_secret_as_env_variable(p_client,
                                                             secret,
                                                             ns,
                                                             keyvaluepair,
                                                             wl_name_create2)


@pytest.fixture(scope='module', autouse="True")
def create_project_client(request):
    client = get_admin_client()
    clusters = client.list_cluster(name=cluster_name).data
    assert len(clusters) == 1
    cluster = clusters[0]
    create_kubeconfig(cluster)
    namespace["cluster"] = cluster

    if upgrade_check_stage == "preupgrade":
        create_project_resources()
    else:
        validate_existing_project_resources()


def create_project_resources():
    cluster = namespace["cluster"]
    p, ns = create_project_and_ns(ADMIN_TOKEN, cluster,
                                  project_name=create_prefix + project_name,
                                  ns_name=create_prefix + ns_name1)
    p_client = get_project_client_for_token(p, ADMIN_TOKEN)

    namespace["p_client"] = p_client
    namespace["ns"] = ns
    namespace["project"] = p
    namespace["testclient_pods"] = []

    # Create pods in existing namespace and new namespace that will be used
    # as test clients from which DNS resolution will be tested

    wlname = create_prefix + "-testsdclient"

    con = [{"name": "test1",
            "image": TEST_CLIENT_IMAGE}]

    workload = p_client.create_workload(name=wlname,
                                        containers=con,
                                        namespaceId=ns.id,
                                        scale=1)
    wait_for_wl_to_active(p_client, workload)
    namespace["workload"] = workload

    pods = wait_for_pods_in_workload(p_client, workload, 1)
    pod = wait_for_pod_to_running(p_client, pods[0])
    namespace["testclient_pods"].append(pod)

    new_ns = create_ns(get_cluster_client_for_token(cluster, ADMIN_TOKEN),
                       cluster, p, ns_name=create_prefix + ns_name2)

    workload = p_client.create_workload(name=wlname,
                                        containers=con,
                                        namespaceId=new_ns.id,
                                        scale=1)
    wait_for_wl_to_active(p_client, workload)
    pods = wait_for_pods_in_workload(p_client, workload, 1)
    pod = wait_for_pod_to_running(p_client, pods[0])
    namespace["testclient_pods"].append(pod)
    assert len(namespace["testclient_pods"]) == 2


def validate_existing_project_resources():
    cluster = namespace["cluster"]
    p_name = validate_prefix + project_name
    ns_name = validate_prefix + ns_name1
    ns2_name = validate_prefix + ns_name2

    # Get existing project
    client = get_admin_client()
    projects = client.list_project(name=p_name,
                                   clusterId=cluster.id).data
    assert len(projects) == 1
    project = projects[0]

    c_client = get_cluster_client_for_token(cluster, ADMIN_TOKEN)
    p_client = get_project_client_for_token(project, ADMIN_TOKEN)

    # Get existing namespace
    nss = c_client.list_namespace(name=ns_name).data
    assert len(nss) == 1
    ns = nss[0]

    # 2nd namespace
    nss = c_client.list_namespace(name=ns2_name).data
    assert len(nss) == 1
    ns2 = nss[0]

    # Get existing SD client pods
    workload_name = validate_prefix + "-testsdclient"
    workloads = p_client.list_workload(name=workload_name,
                                       namespaceId=ns.id).data
    assert len(workloads) == 1
    wl1_pods = p_client.list_pod(workloadId=workloads[0].id).data
    assert len(wl1_pods) == 1

    workload_name = validate_prefix + "-testsdclient"

    workloads = p_client.list_workload(name=workload_name,
                                       namespaceId=ns2.id).data
    assert len(workloads) == 1
    wl2_pods = p_client.list_pod(workloadId=workloads[0].id).data
    assert len(wl2_pods) == 1

    namespace["p_client"] = p_client
    namespace["ns"] = ns
    namespace["project"] = project
    namespace["testclient_pods"] = [wl1_pods[0], wl2_pods[0]]
