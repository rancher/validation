from common import *   # NOQA
from lib.aws import AmazonWebServices
import requests

AGENT_REG_CMD = os.environ.get('RANCHER_AGENT_REG_CMD', "")
HOST_COUNT = int(os.environ.get('RANCHER_HOST_COUNT', 1))
HOST_NAME = os.environ.get('RANCHER_HOST_NAME', "testsa")
RANCHER_SERVER_VERSION = os.environ.get('RANCHER_SERVER_VERSION', "master")
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', "None")
AWS_SSH_KEY_NAME = os.environ.get('AWS_SSH_KEY_NAME', "jenkins-rke-validation")
rke_config = {"authentication": {"type": "authnConfig", "strategy": "x509"},
              "ignoreDockerVersion": False,
              "network": {"type": "networkConfig", "plugin": "canal"},
              "type": "rancherKubernetesEngineConfig"
              }
env_file = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "rancher_env.config")


def test_add_custom_host():
    aws_nodes = AmazonWebServices().create_multiple_nodes(
        HOST_COUNT, random_test_name("testsa"+HOST_NAME))
    if AGENT_REG_CMD != "":
        for aws_node in aws_nodes:
            aws_node.execute_command(AGENT_REG_CMD)


def test_deploy_rancher_server():
    RANCHER_SERVER_CMD = \
        "docker run -d --restart=unless-stopped -p 80:80 -p 443:443 " + \
        "rancher/rancher"
    RANCHER_SERVER_CMD += ":" + RANCHER_SERVER_VERSION
    aws_nodes = AmazonWebServices().create_multiple_nodes(
        1, random_test_name("testsa"+HOST_NAME))
    aws_nodes[0].execute_command(RANCHER_SERVER_CMD)
    time.sleep(120)
    RANCHER_SERVER_URL = "https://" + aws_nodes[0].public_ip_address
    print RANCHER_SERVER_URL
    wait_until_active(RANCHER_SERVER_URL)
    token = get_admin_token(RANCHER_SERVER_URL)
    aws_nodes = \
        AmazonWebServices().create_multiple_nodes(
            5, random_test_name("testcustom"))
    node_roles = [["controlplane"], ["etcd"],
                  ["worker"], ["worker"], ["worker"]]
    client = cattle.Client(url=RANCHER_SERVER_URL+"/v3",
                           token=token, verify=False)
    cluster = client.create_cluster(name=random_name(),
                                    driver="rancherKubernetesEngine",
                                    rancherKubernetesEngineConfig=rke_config)
    assert cluster.state == "active"
    i = 0
    for aws_node in aws_nodes:
        docker_run_cmd = \
            get_custom_host_registration_cmd(client, cluster, node_roles[i],
                                             aws_node)
        aws_node.execute_command(docker_run_cmd)
        i += 1
    validate_cluster_state(client, cluster)
    env_details = "env.CATTLE_TEST_URL='" + RANCHER_SERVER_URL + "'\n"
    env_details += "env.ADMIN_TOKEN='" + token + "'\n"
    file = open(env_file, "w")
    file.write(env_details)
    file.close()


def test_delete_automation_instances():
    filters = [
            {'Name': 'tag:Name', 'Values': ['testsa*', 'testcustom*']},
            {'Name': 'key-name', 'Values': [AWS_SSH_KEY_NAME]}]
    aws_nodes = AmazonWebServices().get_nodes(filters)
    AmazonWebServices().delete_nodes(aws_nodes)


def get_admin_token(RANCHER_SERVER_URL):
    """Returns a ManagementContext for the default global admin user."""
    CATTLE_AUTH_URL = \
        RANCHER_SERVER_URL + "/v3-public/localproviders/local?action=login"
    r = requests.post(CATTLE_AUTH_URL, json={
        'username': 'admin',
        'password': 'admin',
        'responseType': 'json',
    }, verify=False)
    print r.json()
    token = r.json()['token']
    print token
    # Change admin password
    client = cattle.Client(url=RANCHER_SERVER_URL+"/v3",
                           token=token, verify=False)
    admin_user = client.list_user(username="admin")
    admin_user[0].setpassword(newPassword=ADMIN_PASSWORD)

    # Set server-url settings
    serverurl = client.list_setting(name="server-url")
    client.update(serverurl[0], value=RANCHER_SERVER_URL)
    return token


def wait_until_active(rancher_url, timeout=120):
    start = time.time()
    while check_for_no_access(rancher_url):
        time.sleep(.5)
        print "No access yet"
        if time.time() - start > timeout:
            raise Exception('Timed out waiting for Rancher server '
                            'to become active')
    return


def check_for_no_access(rancher_url):
    try:
        requests.get(rancher_url, verify=False)
        return False
    except requests.ConnectionError:
        return True
