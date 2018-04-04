import random
import time
import inspect
import os
import cattle


DEFAULT_TIMEOUT=45
CATTLE_TEST_URL = os.environ.get('CATTLE_TEST_URL', "http://localhost:80")
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', "None")

CATTLE_API_URL = CATTLE_TEST_URL +"/v3"

CATTLE_AUTH_URL = CATTLE_TEST_URL + "/v3-public/localproviders/local?action=login"


def random_str():
    return 'random-{0}-{1}'.format(random_num(), int(time.time()))


def random_num():
    return random.randint(0, 1000000)


def random_int(start, end):
    return random.randint(start, end)


def random_test_name(name="test"):
    return name+"-"+str(random_int(10000, 99999))


def get_admin_client():
    return cattle.Client(url=CATTLE_API_URL, token=ADMIN_TOKEN, verify=False)


def get_client_for_token(token):
    return cattle.Client(url=CATTLE_API_URL, token=token, verify=False)


def get_project_client_for_token(project, token):
    p_url = project.links['self'] + '/schemas'
    p_client = cattle.Client(url=p_url, token=token, verify=False)
    return p_client


def get_cluster_client_for_token(cluster, token):
    c_url = cluster.links['self'] + '/schemas'
    c_client = cattle.Client(url=c_url, token=token, verify=False)
    return c_client


def up(cluster, token):
    c_url = cluster.links['self'] + '/schemas'
    c_client = cattle.Client(url=c_url, token=token, verify=False)
    return c_client


def wait_state(client, obj, state, timeout=DEFAULT_TIMEOUT):
    wait_for(lambda: client.reload(obj).state == state, timeout)
    return client.reload(obj)


def wait_for_condition(client, resource, check_function, fail_handler=None,
                       timeout=DEFAULT_TIMEOUT):
    start = time.time()
    resource = client.reload(resource)
    while not check_function(resource):
        if time.time() - start > timeout:
            exceptionMsg = 'Timeout waiting for ' + resource.baseType + \
                ' to satisfy condition: ' + \
                inspect.getsource(check_function)
            if (fail_handler):
                exceptionMsg = exceptionMsg + fail_handler(resource)
            raise Exception(exceptionMsg)

        time.sleep(.5)
        resource = client.reload(resource)

    return resource


def wait_for(callback, timeout=DEFAULT_TIMEOUT, timeout_message=None):
    start = time.time()
    ret = callback()
    while ret is None or ret is False:
        time.sleep(.5)
        if time.time() - start > timeout:
            if timeout_message:
                raise Exception(timeout_message)
            else:
                raise Exception('Timeout waiting for condition')
        ret = callback()
    return ret

def random_name():
    return "test" + "-" + str(random_int(10000,99999))


def create_project_and_ns(token, cluster):
    client = get_client_for_token(token)
    p = create_project(client, cluster)
    c_client = get_cluster_client_for_token(cluster, token)
    ns = create_ns(c_client, cluster, p)
    return p, ns


def create_project(client, cluster):
    p = client.create_project(name=random_name(),
                              clusterId=cluster.id)
    p = client.wait_success(p)
    assert p.state == 'active'
    return p


def create_ns(client, cluster, project):
    ns = client.create_namespace(name=random_name(),
                                 clusterId=cluster.id,
                                 projectId=project.id)
    #ns = wait_state(client, ns, "state", "active")
    time.sleep(3)
    ns = client.reload(ns)
    assert ns.state == 'active'
    return ns


def assign_members_to_cluster(client, user, cluster, role_template_id):
    crtb = client.create_cluster_role_template_binding(
        clusterId=cluster.id,
        roleTemplateId=role_template_id,
        subjectKind="User",
        userId=user.id)
    return crtb


def assign_members_to_project(client, user, project, role_template_id):
    prtb = client.create_project_role_template_binding(
        projectId=project.id,
        roleTemplateId=role_template_id,
        subjectKind="User",
        userId=user.id)
    return prtb


def change_member_role_in_cluster(client, user, crtb, role_template_id):
    crtb = client.update(crtb,
        roleTemplateId=role_template_id,
        userId=user.id)
    return crtb


def change_member_role_in_project(client, user, prtb, role_template_id):
    prtb = client.update(prtb,
        roleTemplateId=role_template_id,
        userId=user.id)
    return prtb

