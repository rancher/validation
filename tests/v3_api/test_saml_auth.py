from common import *   # NOQA

import requests
import pytest
import json

AUTH_PROVIDER = os.environ.get('AUTH_PROVIDER', "")

# Config Fields
DISPLAYNAME_FIELD = os.environ.get("DISPLAYNAME_FIELD")
GROUPS_FIELD = os.environ.get("GROUPS_FIELD")
IDP_METADATA_CONTENT = os.environ.get("IDP_METADATA_CONTENT")
RANCHER_API_HOST = os.environ.get("RANCHER_API_HOST")
SP_CERT = os.environ.get("SP_CERT")
SP_KEY = os.environ.get("SP_KEY")
UID_FIELD = os.environ.get("UID_FILED")
USERNAME_FIELD = os.environ.get("USERNAME_FIELD")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

CATTLE_AUTH_PROVIDER_URL = RANCHER_API_HOST + "/v3/"+AUTH_PROVIDER+"Configs/" + AUTH_PROVIDER.lower()
CATTLE_AUTH_ENABLE_URL = CATTLE_AUTH_PROVIDER_URL + "?action=testAndEnable"
CATTLE_AUTH_DISABLE_URL = CATTLE_AUTH_PROVIDER_URL + "?action=disable"

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


def test_get_redirect_url_keycloak():
    config_keycloak_fields(ADMIN_TOKEN)
    get_keycloak_redirect_url(ADMIN_TOKEN)


def config_keycloak_fields(token, expected_status=200):
    headers = {'Authorization': 'Bearer ' + token}
    r = requests.put(CATTLE_AUTH_PROVIDER_URL, json={
        "keyCloakConfig": {
            "accessMode": "unrestricted",
            "displayNameField": "surname",
            "enabled": False,
            "groupsField": "Role",
            "idpMetadataContent": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n<EntityDescriptor entityID=\"http://165.227.49.230/auth/realms/amp\"\r\n                   xmlns=\"urn:oasis:names:tc:SAML:2.0:metadata\"\r\n                   xmlns:dsig=\"http://www.w3.org/2000/09/xmldsig#\"\r\n                   xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\r\n   <IDPSSODescriptor WantAuthnRequestsSigned=\"false\"\r\n      protocolSupportEnumeration=\"urn:oasis:names:tc:SAML:2.0:protocol\">\r\n      <SingleLogoutService\r\n         Binding=\"urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST\"\r\n         Location=\"http://165.227.49.230/auth/realms/amp/protocol/saml\" />\r\n      <SingleLogoutService\r\n         Binding=\"urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect\"\r\n         Location=\"http://165.227.49.230/auth/realms/amp/protocol/saml\" />\r\n   <NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:persistent</NameIDFormat>\r\n   <NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:transient</NameIDFormat>\r\n   <NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified</NameIDFormat>\r\n   <NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</NameIDFormat>\r\n\r\n      <SingleSignOnService Binding=\"urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST\"\r\n         Location=\"http://165.227.49.230/auth/realms/amp/protocol/saml\" />\r\n      <SingleSignOnService Binding=\"urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect\"\r\n         Location=\"http://165.227.49.230/auth/realms/amp/protocol/saml\" />\r\n      <KeyDescriptor use=\"signing\">\r\n        <dsig:KeyInfo>\r\n          <dsig:KeyName>DfKVQ64OXG6LPAeyaVXlHHhjUIeG_88sl5UT0R7d6bA</dsig:KeyName>\r\n          <dsig:X509Data>\r\n            <dsig:X509Certificate>MIIClTCCAX0CBgFk8Y8ZbTANBgkqhkiG9w0BAQsFADAOMQwwCgYDVQQDDANhbXAwHhcNMTgwNzMxMTgxNTQ0WhcNMjgwNzMxMTgxNzI0WjAOMQwwCgYDVQQDDANhbXAwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCQWUo3cgn1tPBqThFzDpzr9Jb+r+N/Hxq+LVxbhpGJ8g8GTbvco5w4sGsb4imTUNz51E7UrQ6lfaJuRyNfFwg5jFSngyZhj3xDaygL4BIsG5UrCDb21tX6wzTZhpQtLk97rwwj5EMdhJM1M3PsBDzAyOT2TuAmM1JJEp+JzyGUbAJv2uIUddh7UN3LsTjbQdhr3IcvJTO15rBWymZEjXzvNgedfQyW2WfbA746kC0JdTIj4ljFCMa64gGa2uWRKyBjjRlkf6svx5H0CXbk79yymk/776nyvb2WWBBKmGQ7J/8sP4n2rJ3J7I3ImNc36+eHwuUISko4CTXn9+kQhiGJAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAAeI0i3aN89RPegzk0X2knpQpj88p3dU/xVVNwyx02Ia5EQqx/9wl9a7b+a8E0HiiV2XsHF9lEKXWDVOezCMyL47UwjnqZ6ayA+Z/w6A7Qk2IpQxiH2PukSklaZThEsOv5w9+YdSRAvzSO0Zt17FM3ix7aPTB86E8Jdak1P5XmmzeE+sjEHzYo2/GJ161oeErzne/b+IUykZTaq9JrQNuC+w9nl3eO5UWjhbRp9xJzpKKFO4uvHCMsIkyIqHuHAavTWZXQGxHF9mCYOJTmR+ZZzXMDo/ISZ/5TvlQDfzOU/aT4TP3D2cgWImjwmYc42vMuJiQRydbgRuP5lWhhqmRIE=</dsig:X509Certificate>\r\n          </dsig:X509Data>\r\n        </dsig:KeyInfo>\r\n      </KeyDescriptor>\r\n   </IDPSSODescriptor>\r\n</EntityDescriptor>",
            "name": "keycloak",
            "rancherApiHost": "https://81902f7c.ngrok.io",
            "spCert": "-----BEGIN CERTIFICATE-----\r\nMIIECTCCAvGgAwIBAgIJAI05qopuWFh1MA0GCSqGSIb3DQEBCwUAMGAxCzAJBgNV\r\nBAYTAlVTMQswCQYDVQQIEwJDQTESMBAGA1UEBxMJQ3VwZXJ0aW5vMRAwDgYDVQQK\r\nEwdSYW5jaGVyMQwwCgYDVQQLEwMxMjMxEDAOBgNVBAMTB3JhbmNoZXIwHhcNMTgw\r\nODAzMTc1ODM0WhcNMTkwODAzMTc1ODM0WjBgMQswCQYDVQQGEwJVUzELMAkGA1UE\r\nCBMCQ0ExEjAQBgNVBAcTCUN1cGVydGlubzEQMA4GA1UEChMHUmFuY2hlcjEMMAoG\r\nA1UECxMDMTIzMRAwDgYDVQQDEwdyYW5jaGVyMIIBIjANBgkqhkiG9w0BAQEFAAOC\r\nAQ8AMIIBCgKCAQEA9JeGobVJY35Z1rn4SLjlIm0BJAgwPS6KK8ad0A5J/8XhZqIZ\r\nor6cwmX7kX80cRU9ahC/Ass4WrMrtwxmn5JCBK7e9rAFhKiZobqpNc36cr9vDwm1\r\nBbBZtavP/GWyp80hCKcTGMAghpapWnxn9KqiDxV/TD5e7gWfjyftIo7QwGxgmdYp\r\nQ2jokaAxbPO28KeVfkcI6VjH5wgiAD5Bd5oWYPcWxByyi/3seKvAN9oKkNP3u7Os\r\nxRPBdf2Vzdj4CbdS3rQEApsHHHaiVBI8SvqW3mIXA/9WskBzEc06BhlelHQaW/o7\r\nu113DHnOOzEPIATkezXP39t6vNUFfnx3GCLbywIDAQABo4HFMIHCMB0GA1UdDgQW\r\nBBQxoLoAVccw/2ilBi1+DmN/XNNYSTCBkgYDVR0jBIGKMIGHgBQxoLoAVccw/2il\r\nBi1+DmN/XNNYSaFkpGIwYDELMAkGA1UEBhMCVVMxCzAJBgNVBAgTAkNBMRIwEAYD\r\nVQQHEwlDdXBlcnRpbm8xEDAOBgNVBAoTB1JhbmNoZXIxDDAKBgNVBAsTAzEyMzEQ\r\nMA4GA1UEAxMHcmFuY2hlcoIJAI05qopuWFh1MAwGA1UdEwQFMAMBAf8wDQYJKoZI\r\nhvcNAQELBQADggEBABT+1XfTeDw6Qqjo5585GVf1Q6Wcax3Wyb/2TEdsXEYLuu2p\r\nu5tpXiby+0QOOfgPIQqaRc07dunWYmVCO9R2mmj/7VhPhfU9j/Ol6d1Yv9DANzea\r\nDvu1DeEKfGGF/Kvdmx9a4otYHHrVnPPK9didvrtrYmwMhf7pZWIwyanqOfLhytIH\r\nKHoKKadU2DCuxpAPDKXQZmCJAjiF2QyiDf9S8tCw+gUVlAGAhWAYHdyh1XhKXXTy\r\n7lOfRQye3jpwEpswZAYsz8iaHvKXjwv0exVC+b8xSgMTEpq24opqV3hQKjhB/Eys\r\nS/qamttI5Zi2m07WQXeL4r5eUMNpwLaoFIPskM4=\r\n-----END CERTIFICATE-----",
            "spKey": "-----BEGIN RSA PRIVATE KEY-----\r\nMIIEpAIBAAKCAQEA9JeGobVJY35Z1rn4SLjlIm0BJAgwPS6KK8ad0A5J/8XhZqIZ\r\nor6cwmX7kX80cRU9ahC/Ass4WrMrtwxmn5JCBK7e9rAFhKiZobqpNc36cr9vDwm1\r\nBbBZtavP/GWyp80hCKcTGMAghpapWnxn9KqiDxV/TD5e7gWfjyftIo7QwGxgmdYp\r\nQ2jokaAxbPO28KeVfkcI6VjH5wgiAD5Bd5oWYPcWxByyi/3seKvAN9oKkNP3u7Os\r\nxRPBdf2Vzdj4CbdS3rQEApsHHHaiVBI8SvqW3mIXA/9WskBzEc06BhlelHQaW/o7\r\nu113DHnOOzEPIATkezXP39t6vNUFfnx3GCLbywIDAQABAoIBAQCSqEiRraHThm9X\r\n0SqOcE7z1WhZso86IC25Ed6OYgL82inM4GV+r8xOw9eT5jILnDC26FOf2TpxJ/2O\r\nRGFETO5I4JHQWLr2UCHOV54eJOOG6kItQiTIxHUF+X88V75H3zdveL56mLjn+m6R\r\nUwcCLU3+vWUW0k8ZaUXDEK2fiwKgXS9y3GuSX3HszWrKiGi/61upFIdu4pvEbmSp\r\niMi/zQfdQkrolGhzq+SupOGvQlrxqHt6PkZOpvI6xYm84s81lg/5VB/+pZhWzVIF\r\nHl1PQwTQ1JTXIRjsuyW5trmVwD1iRyz7jSJYucL2emFyBycRirRrubMXlOKR/pNi\r\nuJzZhrgBAoGBAP20Dz92oFxED311HC4M89GBDxrPmahyuIrvzU0HdlK0p+h+95t8\r\nVVRJilqlJvUFAi1O8paIKMtJEyTDAlLOkVlN9JLZvLSdGPw+oadXcaT4Nxq8oBEK\r\nVd7hKVyt0mqbkVwfQOLYMh3iEDbxau9hR5kIep5lcYgZCKVxoLVimxPTAoGBAPbO\r\nWeTopX9MUZd11zNc5nPNymBRwmOT7pe+AiN/AfFCwf51uP3+A77JVdMYuAVdGaCB\r\nOZQRrap9cD/T7epIqhuncboAY5e7k5Wz+l0ziGWttz+Juxo0SzAyihjivafdVo1w\r\nC7TIuBfPHs2eJds001qFMWcmjq0swUqRyJSPxjUpAoGBAN9Fs5WahI4up6M1iVNN\r\nutXJys1Bnm0MaTR8ziTYSF2I96w48Rg5V68R+VzEs4A2pC/TptKriZs9+EcGB+lw\r\nOaJqZK9ISDZ7ex2i0QlAf5c7iuNQ1V2pxuCbL5eMsf14Y3i7WJNKyPBbnwF7fSym\r\nZChduevkQwIPZfiUA2ceHHRZAoGAdbEpRPN8GBw4vFVBbgjbDFYSL6RNYlbk7A97\r\nzZl/P6FqCQHyWYyMFKrF9ohPGJ+w3M1Cu81CV47BvG4/gf1swQs0PFJ7K5wTYMwW\r\nk+NDI9mXDQGM644MXMt89ykI78eowoGv02H0B8aJFdxYiRPDxeLGED5ew04YTor+\r\nb3mwNyECgYA2lQTbyyDoeUXgJqgDMJ3t66CU3WtA7xAYgqaMR0gK31MlMbltBAxF\r\njG57b9zuH0VOYVTQpaysORpfWrHb6nZy8Y1Qq8VaMMwyvdQcwKYVUeiDsxbLVl8y\r\nGKNZ3UoNXx1nIQ0yMaJjjxcta1O+3LrmRWLkKdk23K63JDx7Mo7VNw==\r\n-----END RSA PRIVATE KEY-----",
            "type": "keyCloakConfig",
            "uidField": "email",
            "userNameField": "firstname",
        }
    }, verify=False, headers=headers)
    assert r.status_code == expected_status


def get_keycloak_redirect_url(token, expected_status=200):
    headers = {'Authorization': 'Bearer ' + token}
    r = requests.post(CATTLE_AUTH_ENABLE_URL, json={
        "finalRedirectUrl": "https://81902f7c.ngrok.io"
    }, verify=False, headers=headers)
    assert r.status_code == expected_status
    if expected_status == 200:
        idp_redirect_url = r.json()['idpRedirectUrl']
        print idp_redirect_url
    return idp_redirect_url


# @pytest.fixture(scope='module', autouse="True")
# def create_project_client(request):
#     if AUTH_PROVIDER not in ("keyCloak", "ping"):
#         assert False, "Auth Provider set is not supported"
#     setup["auth_setup_data"] = load_setup_data()
#     client = get_admin_client()
#     clusters = client.list_cluster()
#     assert len(clusters) >= 2
#     cluster1 = clusters[0]
#     for project in client.list_project():
#         delete_existing_users_in_project(client, project)
#     p1, ns1 = create_project_and_ns(ADMIN_TOKEN, cluster1)
#     cluster2 = clusters[1]
#     p2, ns2 = create_project_and_ns(ADMIN_TOKEN, cluster2)
#     setup["cluster1"] = cluster1
#     setup["project1"] = p1
#     setup["ns1"] = ns1
#     setup["cluster2"] = cluster2
#     setup["project2"] = p2
#     setup["ns2"] = ns2
#
#     def fin():
#         client = get_admin_client()
#         client.delete(setup["project1"])
#         client.delete(setup["project2"])
#         delete_cluster_users()
#     request.addfinalizer(fin)


def delete_existing_users_in_cluster(client, cluster):
    crtbs = client.list_cluster_role_template_binding(clusterId=cluster.id)
    for crtb in crtbs:
        client.delete(crtb)


def delete_existing_users_in_project(client, project):
    prtbs = client.list_project_role_template_binding(projectId=project.id)
    for prtb in prtbs:
        client.delete(prtb)

def delete_cluster_users():
    delete_existing_users_in_cluster(get_admin_client(), setup["cluster1"])
    delete_existing_users_in_cluster(get_admin_client(), setup["cluster2"])


def delete_project_users():
    delete_existing_users_in_project(get_admin_client(), setup["project1"])
    delete_existing_users_in_project(get_admin_client(), setup["project2"])


def load_setup_data():
    auth_setup_file = open(auth_setup_fname)
    auth_setup_str = auth_setup_file.read()
    auth_setup_data = json.loads(auth_setup_str)
    return auth_setup_data

