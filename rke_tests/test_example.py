from conftest import *  # NOQA
from common import *


def test_example_one(test_name, cloud_provider, rke_client, kubectl):
    rke_template = 'cluster_3node_template.yml.j2'
    create_and_validate_rke_cluster(
        test_name, cloud_provider, rke_client, kubectl, rke_template, 3)


def test_example_two(test_name, cloud_provider, rke_client, kubectl):
    rke_template = 'minimal_cluster_template.yml.j2'
    create_and_validate_rke_cluster(
        test_name, cloud_provider, rke_client, kubectl, rke_template, 1)
