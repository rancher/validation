from common import *
import pytest


namespace = {"p_client": None, "ns": None, "cluster": None,  "project": None}


def test_wl_sidekick():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
           "image": "sangeetha/testclient"}]
    name = random_test_name("sidekick")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id)
    validate_workload(p_client, workload, "deployment", ns.name)
    side_con = {"name": "test2",
                "image": "sangeetha/testnewhostrouting"}
    con.append(side_con)
    workload = p_client.update(workload,
                               containers=con)
    time.sleep(60)
    validate_workload_with_sidekicks(p_client, workload, "deployment", ns.name)


def test_wl_deployment():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
           "image": "sangeetha/testclient"}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id)
    validate_workload(p_client, workload, "deployment", ns.name)


def test_wl_statefulset():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
           "image": "sangeetha/testclient"}]
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
           "image": "sangeetha/testclient"}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        daemonSetConfig={})
    schedulable_node_count = len(get_schedulable_nodes(cluster))
    validate_workload(p_client, workload, "daemonSet", ns.name, schedulable_node_count)


def test_wl_cronjob():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
           "image": "sangeetha/testclient"}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        cronJobConfig={
                                            "concurrencyPolicy":"Allow",
                                            "failedJobsHistoryLimit":10,
                                            "schedule":"*/1 * * * *",
                                            "successfulJobsHistoryLimit":10})
    validate_workload(p_client, workload, "cronJob", ns.name)


@pytest.fixture(scope='module', autouse="True")
def create_project_client(request):
    client = get_admin_client()
    clusters = client.list_cluster()
    assert len(clusters) >= 1
    cluster = clusters[0]
    create_kubeconfig(cluster)
    p, ns = create_project_and_ns(ADMIN_TOKEN, cluster)
    p_client = get_project_client_for_token(p, ADMIN_TOKEN)
    namespace["p_client"] = p_client
    namespace["ns"] = ns
    namespace["cluster"] = cluster
    namespace["project"] = p
    def fin():
        client = get_admin_client()
        client.delete(namespace["project"])
    request.addfinalizer(fin)
