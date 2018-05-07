from common import *
import pytest
namespace = {"p_client": None, "ns": None, "cluster": None,  "project": None}
random_password = random_test_name("pass")


def test_connectivity_between_pods():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    cluster = namespace["cluster"]

    con = [{"name": "test1",
           "image": "sangeetha/testclient:v2",
           "ports":[],
            "environment":{"ROOT_PASSWORD": random_password}
            }]
    name = random_test_name("default")
    schedulable_node_count = len(get_schedulable_nodes(cluster))

    # Check connectivity between pods in the same namespace

    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        daemonSetConfig={})
    validate_workload(p_client, workload, "daemonSet", ns.name, schedulable_node_count)
    check_connectivity_between_workload_pods(p_client, workload, random_password)

    # Create another namespace in the same project
    # Deploy workloads in this namespace
    # Check that pods belonging to different namespace within the same project can communicate

    c_client = get_cluster_client_for_token(cluster, ADMIN_TOKEN)
    ns1 = create_ns(c_client, cluster, namespace["project"])
    workload1 = p_client.create_workload(name=name,
                                         containers=con,
                                         namespaceId=ns1.id,
                                         daemonSetConfig={})
    validate_workload(p_client, workload1, "daemonSet", ns1.name, schedulable_node_count)

    check_connectivity_between_workload_pods(p_client, workload1, random_password)
    check_connectivity_between_workloads(p_client, workload, p_client, workload1, random_password)

    # Create new project in the same cluster
    # Create namespace and deploy workloads
    # Check that pods belonging to different namespace across different projects cannot communicate

    p2, ns2 = create_project_and_ns(ADMIN_TOKEN, cluster)
    p2_client = get_project_client_for_token(p2, ADMIN_TOKEN)

    workload2 = p2_client.create_workload(name=name,
                                          containers=con,
                                          namespaceId=ns2.id,
                                          daemonSetConfig={})
    validate_workload(p2_client, workload2, "daemonSet", ns2.name, schedulable_node_count)

    check_connectivity_between_workload_pods(p2_client, workload2, random_password)
    check_connectivity_between_workloads(p_client, workload, p2_client, workload2,
                                         random_password, allow_connectivity=False)


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