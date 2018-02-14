from common import *
import pytest
import subprocess
import json

namespace = {"p_client": None, "ns": None}
kube_fname = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          "k8s_kube_config")


def test_wl_sidekick():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
           "image": "sangeetha/testclient"}]
    name = random_test_name("sidekick")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id)
    workloads = p_client.list_workload(uuid=workload.uuid)
    assert len(workloads) == 1
    assert workloads[0].name == name
    time.sleep(10)
    side_con = {"name": "test2",
                "image": "sangeetha/testnewhostrouting"}
    con.append(side_con)
    workload = p_client.update(workload,
                               containers=con)


def test_wl_deployment():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
           "image": "sangeetha/testclient"}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id)
    workloads = p_client.list_workload(uuid=workload.uuid)
    assert len(workloads) == 1
    assert workloads[0].name == name
    validate_workload(name, "deployment", ns.name)


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
    workloads = p_client.list_workload(uuid=workload.uuid)
    assert len(workloads) == 1
    assert workloads[0].name == name
    validate_workload(name, "statefulset", ns.name)


def test_wl_daemonset():
    p_client = namespace["p_client"]
    ns = namespace["ns"]
    con = [{"name": "test1",
           "image": "sangeetha/testclient"}]
    name = random_test_name("default")
    workload = p_client.create_workload(name=name,
                                        containers=con,
                                        namespaceId=ns.id,
                                        daemonSetConfig={})
    workloads = p_client.list_workload(uuid=workload.uuid)
    assert len(workloads) == 1
    assert workloads[0].name == name
    validate_workload(name, "daemonset", ns.name)


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
                                            "schedule":"*/10 * * * *",
                                            "successfulJobsHistoryLimit":10})
    workloads = p_client.list_workload(uuid=workload.uuid)
    assert len(workloads) == 1
    assert workloads[0].name == name
    validate_workload(name, "cronjob", ns.name)


@pytest.fixture(scope='module', autouse="True")
def create_project_client():
    client = get_admin_client()
    clusters = client.list_cluster()
    assert len(clusters) >= 1
    cluster = clusters[0]
    create_kubeconfig(cluster)
    p, ns = create_project_and_ns(ADMIN_TOKEN, cluster)
    p_client = get_project_client_for_token(p, ADMIN_TOKEN)
    namespace["p_client"] = p_client
    namespace["ns"] = ns


def create_kubeconfig(cluster):
    generateKubeConfigOutput = cluster.generateKubeconfig()
    print generateKubeConfigOutput.config
    file = open(kube_fname, "w")
    file.write(generateKubeConfigOutput.config)
    file.close()


def validate_workload(name, type , namespace):
    result = execute_kubectl_cmd("get " + type +" -n " +namespace)
    print result
    assert name in result


def execute_kubectl_cmd(cmd, json_out=False):
    command = 'kubectl --kubeconfig {0} {1}'.format(
        kube_fname, cmd)
    if json_out:
        command += ' -o json'
    result = run_command(command)
    return result


def run_command(command):
    output = subprocess.check_output(command, shell=True)
    return output
    """
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return p.stdout.readline
    """