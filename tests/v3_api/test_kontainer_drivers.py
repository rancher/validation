import sys
import os
import time
from .common import wait_for_condition, get_admin_client, validate_cluster, cluster_cleanup, random_test_name, find_condition, wait_for

CREDENTIALS = os.environ.get('RANCHER_GKE_CREDENTIAL', "")
GKE_MASTER_VERSION = os.environ.get('RANCHER_GKE_MASTER_VERSION', "")


def test_create_cluster_with_kontainer_driver(request):
    client = get_admin_client()
    driver = client.create_kontainer_driver({
        "active": True,
        "baseType": "kontainerDriver",
        "builtIn": False,
        "url": "https://github.com/nathan-jenan-rancher/kontainer-engine-example-driver/releases/download/updategke/kontainer-engine-driver-example-" + sys.platform,
        "createDynamicSchema": True
    })

    request.addfinalizer(lambda: client.delete(driver))

    driver = wait_for_condition(
        client, driver,
        lambda x: find_condition(x, 'Active') == "True",
        lambda x: 'Condition is: ' + find_condition(x, 'Active'))

    credentialdata = open(CREDENTIALS, 'r').read()

    cluster_body = {
        "dockerRootDir": "/var/lib/docker",
        "enableNetworkPolicy": False,
        "type": "cluster",
        "exampleEngineConfig": {
            "clusterIpv4Cidr": "",
            "description": "",
            "diskSizeGb": 100,
            "displayName": "",
            "driverName": driver.id,
            "enableAlphaFeature": False,
            "enableHorizontalPodAutoscaling": True,
            "enableHttpLoadBalancing": True,
            "enableKubernetesDashboard": False,
            "enableLegacyAbac": "",
            "enableNetworkPolicyConfig": True,
            "enableStackdriverLogging": True,
            "enableStackdriverMonitoring": True,
            "gkeCredentialPath": "",
            "imageType": "",
            "kubernetesDashboard": False,
            "legacyAuthorization": False,
            "machineType": "g1-small",
            "maintenanceWindow": "",
            "masterVersion": "1.11.2-gke.18",
            "name": "asdf",
            "network": "",
            "nodeCount": 1,
            "nodePool": "",
            "nodeVersion": "",
            "projectId": "rancher-dev",
            "subNetwork": "",
            "zone": "us-central1-f",
            "type": "exampleEngineConfig",
            "credential": credentialdata
        },
        "name": random_test_name("testkontainerdrivers")
    }

    cluster = client.create_cluster(cluster_body)

    def cluster_not_exist():
        return client.by_id_cluster(cluster.id) is None

    def delete_cluster_and_wait():
        cluster_cleanup(client, cluster)
        wait_for(cluster_not_exist)

    request.addfinalizer(delete_cluster_and_wait)

    cluster = wait_for_condition(
        client, cluster,
        lambda x: x.state == "active",
        lambda x: 'State is: ' + x.state)

    cluster = validate_cluster(client, cluster, check_intermediate_state=True,
                               skipIngresscheck=True)
