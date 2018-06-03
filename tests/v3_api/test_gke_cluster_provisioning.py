from common import *   # NOQA


CREDENTIALS = os.environ.get('GKE_CREDENTIAL', "")
RANCHER_CLEANUP_CLUSTER = os.environ.get('RANCHER_CLEANUP_CLUSTER', "True")
GKE_MASTER_VERSION = os.environ.get('GKE_MASTER_VERSION', "1.9.7-gke.1")


def test_create_gke_cluster():

    client = get_admin_client()
    gkeConfig = get_gke_config()

    print "Cluster creation"
    cluster = client.create_cluster(gkeConfig)
    clusterid = cluster.id
    print cluster
    print "Cluster list"
    clusterlist = client.list_cluster(clusterId=clusterid)
    cluster = client.reload(clusterlist[0])
    print cluster.state
    cluster = validate_cluster(client, cluster, check_intermediate_state=True,
                               skipIngresscheck=True)

    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)


def test_create_gke_cluster_with_validate_endpoint_ingress():

    client = get_admin_client()
    gkeConfig = get_gke_config()

    print "Cluster creation"
    cluster = client.create_cluster(gkeConfig)
    clusterid = cluster.id
    print cluster
    print "Cluster list"
    clusterlist = client.list_cluster(clusterId=clusterid)
    cluster = client.reload(clusterlist[0])
    print cluster.state

    cluster = validate_cluster(client, cluster, check_intermediate_state=True,
                               skipIngresscheck=True)
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

    name = random_test_name("testingress")
    host = "xip.io"
    path = "/name.html"
    rule = {"host": host,
            "paths":
                {path:
                    {"workloadIds": [workload.id], "targetPort": "80"}}}
    ingress = p_client.create_ingress(name=name,
                                      namespaceId=ns.id,
                                      rules=[rule])
    print ingress
    validate_ingress_using_endpoint(p_client, ingress, [workload],
                                    timeout=600,
                                    ingressactivetimeout=120,
                                    waitforingresslinktobefunctional=1500)

    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)


def readDataFile(data_dir, name):
    fname = os.path.join(data_dir, name)
    print fname
    is_file = os.path.isfile(fname)
    assert is_file
    with open(fname) as f:
        return f.read()


def get_gke_config():

    # Generate the config for GKE cluster
    credfilename = "credential.txt"
    PATH = os.path.dirname(os.path.realpath(__file__))
    credfilepath = PATH + "/" + credfilename

    print GKE_MASTER_VERSION

    f = open(credfilepath, "w")
    f.write(CREDENTIALS)
    f.close()

    credentialdata = readDataFile(os.path.dirname(os.path.realpath(__file__)) +
                                  "/", credfilename)
    print credentialdata
    gkeConfig = {
        "type": "cluster",
        "googleKubernetesEngineConfig": {
            "disableHorizontalPodAutoscaling": False,
            "disableHttpLoadBalancing": False,
            "disableNetworkPolicyConfig": False,
            "diskSizeGb": 10,
            "enableAlphaFeature": False,
            "enableKubernetesDashboard": False,
            "enableLegacyAbac": False,
            "nodeCount": 3,
            "type": "googleKubernetesEngineConfig",
            "machineType": "g1-small",
            "zone": "us-central1-f",
            "clusterIpv4Cidr": " ",
            "credential": credentialdata,
            "projectId": "rancher-qa",
            "masterVersion": GKE_MASTER_VERSION
        },
        "name": "gkeclustertestsoumya"
    }

    return gkeConfig
