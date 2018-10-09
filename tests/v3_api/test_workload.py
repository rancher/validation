import pytest

from .common import *  # NOQA

namespace = {"p_client": None, "ns": None, "cluster": None, "project": None}


def test_wl_sidekick():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
            "image": TEST_CLIENT_IMAGE}]
    name = random_test_name("sidekick")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id)
    validate_workload(p_client, workload, "deployment", ns.name)
    side_con = {"name": "test2",
                "image": TEST_TARGET_IMAGE}
    con.append(side_con)
    workload = p_client.update(workload,
                               containers=con)
    time.sleep(60)
    validate_workload_with_sidekicks(
        p_client, workload, "deployment", ns.name)


def test_wl_deployment():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
            "image": TEST_CLIENT_IMAGE}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id)
    validate_workload(p_client, workload, "deployment", ns.name)


def test_wl_statefulset():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
            "image": TEST_CLIENT_IMAGE}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        statefulSetConfig={}
                                        )
    validate_workload(p_client, workload, "statefulSet", ns.name)


def test_wl_daemonset():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    cluster = namespace["cluster"]
    con = [{"name": "test1",
            "image": TEST_CLIENT_IMAGE}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        daemonSetConfig={})
    schedulable_node_count = len(get_schedulable_nodes(cluster))
    validate_workload(p_client, workload, "daemonSet",
                      ns.name, schedulable_node_count)


def test_wl_cronjob():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
            "image": TEST_CLIENT_IMAGE}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        cronJobConfig={
                                            "concurrencyPolicy": "Allow",
                                            "failedJobsHistoryLimit": 10,
                                            "schedule": "*/1 * * * *",
                                            "successfulJobsHistoryLimit": 10})
    validate_workload(p_client, workload, "cronJob", ns.name)


def test_wl_upgrade():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
            "image": TEST_TARGET_IMAGE}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        scale=2)
    wait_for_pods_in_workload(p_client, workload, 2)
    validate_workload(p_client, workload, "deployment", ns.name, 2)
    revisions = workload.revisions()
    assert len(revisions) == 1
    for revision in revisions:
        if revision["containers"][0]["image"] == TEST_TARGET_IMAGE:
            firstrevision = revision.id

    con = [{"name": "test1",
            "image": "nginx"}]
    p_client.update(workload, containers=con)
    wait_for_pod_images(p_client, workload, ns.name, "nginx", 2)
    wait_for_pods_in_workload(p_client, workload, 2)
    validate_workload(p_client, workload, "deployment", ns.name, 2)
    validate_workload_image(p_client, workload, "nginx", ns)
    revisions = workload.revisions()
    assert len(revisions) == 2
    for revision in revisions:
        if revision["containers"][0]["image"] == "nginx":
            secondrevision = revision.id

    con = [{"name": "test1",
            "image": TEST_CLIENT_IMAGE}]
    p_client.update(workload, containers=con)
    wait_for_pod_images(p_client, workload, ns.name, TEST_CLIENT_IMAGE, 2)
    wait_for_pods_in_workload(p_client, workload, 2)
    validate_workload(p_client, workload, "deployment", ns.name, 2)
    validate_workload_image(p_client, workload, TEST_CLIENT_IMAGE, ns)
    revisions = workload.revisions()
    assert len(revisions) == 3
    for revision in revisions:
        if revision["containers"][0]["image"] == TEST_CLIENT_IMAGE:
            thirdrevision = revision.id

    p_client.action(workload, "rollback", replicaSetId=firstrevision)
    wait_for_pod_images(p_client, workload, ns.name, TEST_TARGET_IMAGE, 2)
    wait_for_pods_in_workload(p_client, workload, 2)
    validate_workload(p_client, workload, "deployment", ns.name, 2)
    validate_workload_image(p_client, workload, TEST_TARGET_IMAGE, ns)

    p_client.action(workload, "rollback", replicaSetId=secondrevision)
    wait_for_pod_images(p_client, workload, ns.name, "nginx", 2)
    wait_for_pods_in_workload(p_client, workload, 2)
    validate_workload(p_client, workload, "deployment", ns.name, 2)
    validate_workload_image(p_client, workload, "nginx", ns)

    p_client.action(workload, "rollback", replicaSetId=thirdrevision)
    wait_for_pod_images(p_client, workload, ns.name, TEST_CLIENT_IMAGE, 2)
    wait_for_pods_in_workload(p_client, workload, 2)
    validate_workload(p_client, workload, "deployment", ns.name, 2)
    validate_workload_image(p_client, workload, TEST_CLIENT_IMAGE, ns)


def test_wl_pod_scale_up():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
            "image": "sangeetha/testclient"}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id)
    workload = wait_for_wl_to_active(p_client, workload)
    for key, value in workload.workloadLabels.items():
        label = key + "=" + value
    get_pods = "get pods -l" + label + " -n " + ns.name
    allpods = execute_kubectl_cmd(get_pods)
    wait_for_pods_in_workload(p_client, workload, 1)

    p_client.update(workload, scale=2, containers=con)
    validate_workload(p_client, workload, "deployment", ns.name, 2)
    validate_pods_are_running_by_id(allpods, workload, ns.name)

    for key, value in workload.workloadLabels.items():
        label = key + "=" + value
    allpods = execute_kubectl_cmd(get_pods)
    wait_for_pods_in_workload(p_client, workload, 2)
    p_client.update(workload, scale=3, containers=con)
    validate_workload(p_client, workload, "deployment", ns.name, 3)
    validate_pods_are_running_by_id(allpods, workload, ns.name)


def test_wl_pod_scale_down():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
            "image": "sangeetha/testclient"}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        scale=3)
    wait_for_wl_to_active(p_client, workload)
    wait_for_pods_in_workload(p_client, workload, 3)

    p_client.update(workload, scale=2, containers=con)
    wait_for_pods_in_workload(p_client, workload, 2)
    for key, value in workload.workloadLabels.items():
        label = key + "=" + value
    get_pods = "get pods -l" + label + " -n " + ns.name
    allpods = execute_kubectl_cmd(get_pods)
    validate_workload(p_client, workload, "deployment", ns.name, 2)
    validate_pods_are_running_by_id(allpods, workload, ns.name)

    p_client.update(workload, scale=1, containers=con)
    wait_for_pods_in_workload(p_client, workload, 1)
    for key, value in workload.workloadLabels.items():
        label = key + "=" + value
    allpods = execute_kubectl_cmd(get_pods)
    validate_workload(p_client, workload, "deployment", ns.name)
    validate_pods_are_running_by_id(allpods, workload, ns.name)


def test_wl_pause_orchestration():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
            "image": "sangeetha/testclient"}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        scale=2)
    workload = wait_for_wl_to_active(p_client, workload)
    wait_for_pods_in_workload(p_client, workload, 2)
    p_client.action(workload, "pause")
    validate_workload_paused(p_client, workload, True)
    con = [{"name": "test1",
            "image": "nginx"}]
    p_client.update(workload, containers=con)
    validate_pod_images("sangeetha/testclient", workload, ns.name)
    p_client.action(workload, "resume")
    workload = wait_for_wl_to_active(p_client, workload)
    wait_for_pods_in_workload(p_client, workload, 2)
    validate_workload_paused(p_client, workload, False)
    validate_pod_images("nginx", workload, ns.name)


@pytest.fixture(scope='module', autouse="True")
def create_project_client(request):
    client, cluster = get_admin_client_and_cluster()

    create_kubeconfig(cluster)
    p, ns = create_project_and_ns(ADMIN_TOKEN, cluster, "testworkload")
    p_client = get_project_client_for_token(p, ADMIN_TOKEN)
    namespace["p_client"] = p_client
    namespace["ns"] = ns
    namespace["cluster"] = cluster
    namespace["project"] = p

    def fin():
        client = get_admin_client()
        client.delete(namespace["project"])
    request.addfinalizer(fin)
