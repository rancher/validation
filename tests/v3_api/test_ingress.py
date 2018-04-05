from common import *
import pytest


namespace = {"p_client": None, "ns": None, "cluster": None,  "project": None}

def test_ingress():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    cluster = namespace["cluster"]
    con = [{"name": "test1",
           "image": "sangeetha/testnewhostrouting"}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        daemonSetConfig={})
    validate_workload(p_client, workload, "daemonSet", ns.name, len(get_schedulable_nodes(cluster)))
    host = "test.com"
    path = "/name.html"
    rule = {"host": host,
            "paths":
                {path:
                      {"workloadIds": [workload.id], "targetPort": "80"}}}
    ingress = p_client.create_ingress(name=name,
                                      namespaceId=ns.id,
                                      rules=[rule])
    validate_ingress(namespace["p_client"], namespace["cluster"], workload, host, path )


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


