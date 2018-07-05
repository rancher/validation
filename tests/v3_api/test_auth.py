from common import *   # NOQA

import requests
import pytest
import json

AUTH_PROVIDER = os.environ.get('RANCHER_AUTH_PROVIDER', "")
AD_PERMISSION_DENIED_CODE = 401
LDAP_PERMISSION_DENIED_CODE = 403
PASSWORD = os.environ.get('RANCHER_USER_PASSWORD', "")


CATTLE_AUTH_URL = \
    CATTLE_TEST_URL + \
    "/v3-public/"+AUTH_PROVIDER+"Providers/" + \
    AUTH_PROVIDER.lower()+"?action=login"

CATTLE_AUTH_PROVIDER_URL = \
    CATTLE_TEST_URL + "/v3/"+AUTH_PROVIDER+"Configs/"+AUTH_PROVIDER.lower()

CATTLE_AUTH_PRINCIPAL_URL = CATTLE_TEST_URL + "/v3/principals?action=search"


setup = {"cluster1": None,
         "project1": None,
         "ns1": None,
         "cluster2": None,
         "project2": None,
         "ns2": None,
         "auth_setup_data": None,
         "permission_denied_code": 403}

auth_setup_fname = \
    os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/resource",
                 AUTH_PROVIDER.lower() + ".json")


def test_access_control_required_set_access_mode_required():
    access_mode = "required"
    validate_access_control_set_access_mode(access_mode)


def test_access_control_restricted_set_access_mode_required():
    access_mode = "restricted"
    validate_access_control_set_access_mode(access_mode)


def test_access_control_required_add_users_and_groups_to_cluster():
    access_mode = "required"
    validate_add_users_and_groups_to_cluster_or_project(
        access_mode, add_users_to_cluster=True)


def test_access_control_restricted_add_users_and_groups_to_cluster():
    access_mode = "restricted"
    validate_add_users_and_groups_to_cluster_or_project(
        access_mode, add_users_to_cluster=True)


def test_access_control_required_add_users_and_groups_to_project():
    access_mode = "required"
    validate_add_users_and_groups_to_cluster_or_project(
        access_mode, add_users_to_cluster=False)


def test_access_control_restricted_add_users_and_groups_to_project():
    access_mode = "restricted"
    validate_add_users_and_groups_to_cluster_or_project(
        access_mode, add_users_to_cluster=False)


def validate_access_control_set_access_mode(access_mode):
    delete_cluster_users()
    auth_setup_data = setup["auth_setup_data"]
    admin_user = auth_setup_data["admin_user"]
    token = login(admin_user, PASSWORD)
    allowed_principal_ids = []
    for user in auth_setup_data["allowed_users"]:
        allowed_principal_ids.append(principal_lookup(user, token))
    for group in auth_setup_data["allowed_groups"]:
        allowed_principal_ids.append(principal_lookup(group, token))
    allowed_principal_ids.append(principal_lookup(admin_user, token))

    # Add users and groups in allowed list to access rancher-server
    add_users_to_siteAccess(token, access_mode, allowed_principal_ids)

    for user in auth_setup_data["allowed_users"]:
        login(user, PASSWORD)

    for group in auth_setup_data["allowed_groups"]:
        for user in auth_setup_data[group]:
            login(user, PASSWORD)

    for user in auth_setup_data["dis_allowed_users"]:
        login(user, PASSWORD,
              expected_status=setup["permission_denied_code"])

    for group in auth_setup_data["dis_allowed_groups"]:
        for user in auth_setup_data[group]:
            login(user, PASSWORD,
                  expected_status=setup["permission_denied_code"])

    # Add users and groups from dis allowed list to access rancher-server

    for user in auth_setup_data["dis_allowed_users"]:
        allowed_principal_ids.append(principal_lookup(user, token))

    for group in auth_setup_data["dis_allowed_groups"]:
        for user in auth_setup_data[group]:
            allowed_principal_ids.append(principal_lookup(user, token))

    add_users_to_siteAccess(token, access_mode, allowed_principal_ids)

    for user in auth_setup_data["allowed_users"]:
        login(user, PASSWORD)

    for group in auth_setup_data["allowed_groups"]:
        for user in auth_setup_data[group]:
            login(user, PASSWORD)

    for user in auth_setup_data["dis_allowed_users"]:
        login(user, PASSWORD)

    for group in auth_setup_data["dis_allowed_groups"]:
        for user in auth_setup_data[group]:
            login(user, PASSWORD)

    # Remove users and groups from allowed list to access rancher-server

    allowed_principal_ids = []

    allowed_principal_ids.append(principal_lookup(admin_user, token))

    for user in auth_setup_data["dis_allowed_users"]:
        allowed_principal_ids.append(principal_lookup(user, token))
    for group in auth_setup_data["dis_allowed_groups"]:
        for user in auth_setup_data[group]:
            allowed_principal_ids.append(principal_lookup(user, token))

    add_users_to_siteAccess(token, access_mode, allowed_principal_ids)

    for user in auth_setup_data["allowed_users"]:
        login(user, PASSWORD,
              expected_status=setup["permission_denied_code"])

    for group in auth_setup_data["allowed_groups"]:
        for user in auth_setup_data[group]:
            login(user, PASSWORD,
                  expected_status=setup["permission_denied_code"])

    for user in auth_setup_data["dis_allowed_users"]:
        login(user, PASSWORD)

    for group in auth_setup_data["dis_allowed_groups"]:
        for user in auth_setup_data[group]:
            login(user, PASSWORD)


def validate_add_users_and_groups_to_cluster_or_project(
        access_mode, add_users_to_cluster=True):
    delete_cluster_users()
    client = get_admin_client()
    for project in client.list_project():
        delete_existing_users_in_project(client, project)
    auth_setup_data = setup["auth_setup_data"]
    admin_user = auth_setup_data["admin_user"]
    token = login(admin_user, PASSWORD)
    allowed_principal_ids = []
    allowed_principal_ids.append(principal_lookup(admin_user, token))

    # Add users and groups in allowed list to access rancher-server
    add_users_to_siteAccess(token, access_mode, allowed_principal_ids)

    groups_to_check = []
    users_to_check = []
    if add_users_to_cluster:
        groups_to_check = auth_setup_data["groups_added_to_cluster"]
        users_to_check = auth_setup_data["users_added_to_cluster"]
    else:
        groups_to_check = auth_setup_data["groups_added_to_project"]
        users_to_check = auth_setup_data["users_added_to_project"]
    for group in groups_to_check:
        for user in auth_setup_data[group]:
            login(user, PASSWORD,
                  expected_status=setup["permission_denied_code"])

    for user in users_to_check:
        login(user, PASSWORD,
              expected_status=setup["permission_denied_code"])

    client = get_client_for_token(token)
    for group in groups_to_check:
        if add_users_to_cluster:
            assign_user_to_cluster(client, principal_lookup(group, token),
                                   setup["cluster1"], "cluster-owner")
        else:
            assign_user_to_project(client, principal_lookup(group, token),
                                   setup["project2"], "project-owner")
    for user in users_to_check:
        if add_users_to_cluster:
            assign_user_to_cluster(client, principal_lookup(user, token),
                                   setup["cluster1"], "cluster-owner")
        else:
            assign_user_to_project(client, principal_lookup(user, token),
                                   setup["project2"], "cluster-owner")
    expected_status = setup["permission_denied_code"]

    if access_mode == "required":
        expected_status = setup["permission_denied_code"]

    if access_mode == "restricted":
        expected_status = 201

    for group in groups_to_check:
        for user in auth_setup_data[group]:
            login(user, PASSWORD, expected_status)

    for user in users_to_check:
        login(user, PASSWORD, expected_status)


def login(username, password, expected_status=201):
    token = ""
    r = requests.post(CATTLE_AUTH_URL, json={
        'username': username,
        'password': password,
        'responseType': 'json',
    }, verify=False)
    assert r.status_code == expected_status
    print "Login request for " + username + " " + str(expected_status)
    if expected_status == 201:
        token = r.json()['token']
    return token


def principal_lookup(name, token):
    headers = {'Authorization': 'Bearer ' + token}
    r = requests.post(CATTLE_AUTH_PRINCIPAL_URL,
                      json={'name': name, 'responseType': 'json'},
                      verify=False, headers=headers)
    assert r.status_code == 200
    principals = r.json()['data']
    for principal in principals:
        if principal['principalType'] == "user":
            if principal['loginName'] == name:
                return principal["id"]
        if principal['principalType'] == "group":
            if principal['name'] == name:
                return principal["id"]
    assert False


def add_users_to_siteAccess(token, access_mode, allowed_principal_ids):
    headers = {'Authorization': 'Bearer ' + token}
    r = requests.put(CATTLE_AUTH_PROVIDER_URL, json={
        'allowedPrincipalIds': allowed_principal_ids,
        'accessMode': access_mode,
        'responseType': 'json',
    }, verify=False, headers=headers)
    print r.json()


def assign_user_to_cluster(client, principal_id, cluster, role_template_id):
    crtb = client.create_cluster_role_template_binding(
        clusterId=cluster.id,
        roleTemplateId=role_template_id,
        userPrincipalId=principal_id)
    return crtb


def assign_user_to_project(client, principal_id, project, role_template_id):
    prtb = client.create_project_role_template_binding(
        projectId=project.id,
        roleTemplateId=role_template_id,
        userPrincipalId=principal_id)
    return prtb


def delete_existing_users_in_cluster(client, cluster):
    crtbs = client.list_cluster_role_template_binding(clusterId=cluster.id)
    for crtb in crtbs:
        client.delete(crtb)


def delete_existing_users_in_project(client, project):
    prtbs = client.list_project_role_template_binding(projectId=project.id)
    for prtb in prtbs:
        client.delete(prtb)


@pytest.fixture(scope='module', autouse="True")
def create_project_client(request):
    if AUTH_PROVIDER not in ("activeDirectory", "openLDAP"):
        assert False, "Auth Provider set is not supported"
    setup["auth_setup_data"] = load_setup_data()
    client = get_admin_client()
    clusters = client.list_cluster()
    assert len(clusters) >= 2
    cluster1 = clusters[0]
    for project in client.list_project():
        delete_existing_users_in_project(client, project)
    p1, ns1 = create_project_and_ns(ADMIN_TOKEN, cluster1)
    cluster2 = clusters[1]
    p2, ns2 = create_project_and_ns(ADMIN_TOKEN, cluster2)
    setup["cluster1"] = cluster1
    setup["project1"] = p1
    setup["ns1"] = ns1
    setup["cluster2"] = cluster2
    setup["project2"] = p2
    setup["ns2"] = ns2
    if AUTH_PROVIDER == "activeDirectory":
        setup["permission_denied_code"] = AD_PERMISSION_DENIED_CODE
    if AUTH_PROVIDER == "openLDAP":
        setup["permission_denied_code"] = LDAP_PERMISSION_DENIED_CODE

    def fin():
        client = get_admin_client()
        client.delete(setup["project1"])
        client.delete(setup["project2"])
        delete_cluster_users()
    request.addfinalizer(fin)


def delete_cluster_users():
    delete_existing_users_in_cluster(get_admin_client(), setup["cluster1"])
    delete_existing_users_in_cluster(get_admin_client(), setup["cluster2"])


def load_setup_data():
    auth_setup_file = open(auth_setup_fname)
    auth_setup_str = auth_setup_file.read()
    auth_setup_data = json.loads(auth_setup_str)
    return auth_setup_data
