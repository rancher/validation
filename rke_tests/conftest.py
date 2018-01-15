import os
import pytest

from lib.aws import AmazonWebServices
from lib.rke_client import RKEClient


CLOUD_PROVIDER = os.environ.get("CLOUD_PROVIDER", 'AWS')


@pytest.fixture(scope='session')
def cloud_provider():
    if CLOUD_PROVIDER == 'AWS':
        return AmazonWebServices()


@pytest.fixture(scope='function')
def rke_client():
    return RKEClient()
