from .common import *   # NOQA


CREDENTIALS = os.environ.get('GKE_CREDENTIAL', "")
RANCHER_CLEANUP_CLUSTER = os.environ.get('RANCHER_CLEANUP_CLUSTER', "True")
GKE_MASTER_VERSION = os.environ.get('GKE_MASTER_VERSION', "1.10.7-gke.2")


def test_create_gke_cluster():

    if not CREDENTIALS:
        assert (False), "GKE JSON Credentials not provided, cannot create " \
                        "cluster"
    client = get_admin_client()
    gkeConfig = get_gke_config()

    print("Cluster creation")
    cluster = client.create_cluster(gkeConfig)
    clusterid = cluster.id
    print(cluster)
    print("Cluster list")
    clusterlist = client.list_cluster(clusterId=clusterid).data
    cluster = client.reload(clusterlist[0])
    print(cluster.state)
    cluster = validate_cluster(client, cluster, check_intermediate_state=True,
                               skipIngresscheck=True)

    if RANCHER_CLEANUP_CLUSTER == "True":
        delete_cluster(client, cluster)


def readDataFile(data_dir, name):
    fname = os.path.join(data_dir, name)
    print(fname)
    is_file = os.path.isfile(fname)
    assert is_file
    with open(fname) as f:
        return f.read()


def get_gke_config():

    # Generate the config for GKE cluster
    credfilename = "credential.txt"
    PATH = os.path.dirname(os.path.realpath(__file__))
    credfilepath = PATH + "/" + credfilename

    print(GKE_MASTER_VERSION)

    # The json GKE credentials file is being written to a file and then read

    f = open(credfilepath, "w")
    f.write(CREDENTIALS)
    f.close()

    credentialdata = readDataFile(os.path.dirname(os.path.realpath(__file__)) +
                                  "/", credfilename)
    print(credentialdata)
    gkeConfig = {
        "type": "cluster",
        "googleKubernetesEngineConfig": {
            "diskSizeGb": 100,
            "enableAlphaFeature": False,
            "enableHorizontalPodAutoscaling": True,
            "enableHttpLoadBalancing": True,
            "enableKubernetesDashboard": False,
            "enableLegacyAbac": False,
            "enableNetworkPolicyConfig": True,
            "enableStackdriverLogging": True,
            "enableStackdriverMonitoring": True,
            "masterVersion": GKE_MASTER_VERSION,
            "machineType": "g1-small",
            "type": "googleKubernetesEngineConfig",
            "nodeCount": 3,
            "zone": "us-central1-f",
            "clusterIpv4Cidr": " ",
            "credential": credentialdata,
            "projectId": "rancher-qa",

        },
        "name": "qagkeclustertest",
        "type": "cluster"
    }

    return gkeConfig
