import pytest
import asyncio


from .common import *  # NOQA

namespace = {"p_client": None, "ns": None, "cluster": None, "project": None}


def test_custom_catalog():
    client = get_admin_client()
    url = "https://github.com/guangbochen/validation-charts.git"
    name = random_str()
    catalog = client.create_catalog(name=name,
                                    branch="master",
                                    url=url)
    wait_for_template_to_be_created(client, name)
    catalog2 = client.update(catalog,
                             branch="test-ha-templatesv2")
    print("added new catalog: " + catalog["name"])
    wait_for_template_to_be_created(client, name)
    asyncio.run(main_template_version_new_file(client, name))
    client.delete(catalog2)
    wait_for_template_to_be_deleted(client, name)


async def get_template_version_new_file(client, name, index):
    template_versions = client.by_id_template_version(
        "cattle-global-data:" + name + "-test-ha-templates-0.1.0")
    new_file_name = "test-ha-templates/templates/new.yaml"
    if new_file_name in template_versions["files"]:
        print("found new template file: " + new_file_name
              + ", tried " + str(index+1) + " times")
    else:
        raise AssertionError("failed to found new template file: "
                             + new_file_name + ", tried "
                             + str(index+1) + " times")


async def main_template_version_new_file(client, name):
    await asyncio.gather(*(get_template_version_new_file(client, name, i)
                           for i in range(100)))


def wait_for_template_to_be_created(client, name, timeout=45):
    found = False
    start = time.time()
    interval = 2
    while not found:
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for templates")
        templates = client.list_template(catalogId=name)
        if len(templates) > 0:
            found = True
        time.sleep(interval)
        interval *= 2


def wait_for_template_to_be_deleted(client, name, timeout=45):
    found = False
    start = time.time()
    interval = 0.5
    while not found:
        if time.time() - start > timeout:
            raise AssertionError(
                "Timed out waiting for templates")
        templates = client.list_template(catalogId=name)
        if len(templates) == 0:
            found = True
        time.sleep(interval)
        interval *= 2


@pytest.fixture(scope='module', autouse="True")
def create_project_client(request):
    client, cluster = get_admin_client_and_cluster()
    create_kubeconfig(cluster)
    p, ns = create_project_and_ns(ADMIN_TOKEN, cluster,
                                  random_test_name("catalog-ha"))
    namespace["ns"] = ns
    namespace["cluster"] = cluster
    namespace["project"] = p

    def fin():
        cl = get_admin_client()
        cl.delete(namespace["ns"])
        cl.delete(namespace["project"])
    request.addfinalizer(fin)
