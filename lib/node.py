class Node(object):
    # Model off Rancher Node object
    # {
    #     "created": "2018-01-02T16:15:12Z",
    #     "createdTS": 1514909712000,
    #     "hostname": "minikube",
    #     "info": {
    #         "cpu": {
    #             "count": 2
    #         },
    #         "kubernetes": {
    #             "kubeProxyVersion": "v1.8.0",
    #             "kubeletVersion": "v1.8.0"
    #         },
    #         "memory": {
    #             "memTotalKiB": 2048076
    #         },
    #         "os": {
    #             "dockerVersion": "Unknown",
    #             "kernelVersion": "4.9.13",
    #             "operatingSystem": "Buildroot 2017.02"
    #         }
    #     },
    #     "ipAddress": "192.168.99.100",
    #     "labels": {
    #         "beta.kubernetes.io/arch": "amd64",
    #         "beta.kubernetes.io/os": "linux",
    #         "kubernetes.io/hostname": "minikube"
    #     },
    #     "nodeName": "minikube",
    #     "state": "active",
    # }

    def __init__(
        self, provider_node_id=None, host_name=None, node_name=None,
        public_ip_address=None, private_ip_address=None, state=None,
        labels=None, host_name_override=None, ssh_key=None,
            ssh_key_name=None, ssh_key_path=None, ssh_user=None):

        self.provider_node_id = provider_node_id
        self.node_name = node_name
        self.host_name = host_name
        self.host_name_override = host_name_override
        self.public_ip_address = public_ip_address
        self.private_ip_address = private_ip_address
        self.ssh_user = ssh_user
        self.ssh_key = ssh_key
        self.ssh_key_name = ssh_key_name
        self.ssh_key_path = ssh_key_path
        self.labels = labels or {}
        self.state = state
