# RKE Template Referenece


#### For Nodes, the '{}' should be replace with index starting at 0

FIELD               TEMPLATE_FIELD_NAME
address:            ip_address_{} for IPv4 OR dns_hostname_{} for DNS resolvable name
user:               ssh_user_{}
ssh_key:            ssh_key_{}
ssh_key_path:       ssh_key_path_{} for the path to the ssh key 
internal_address:   internal_address_{}
 
#### All other fields will be replaced if passed in to build_rke_template as key value pairs

FIELD                   TEMPLATE_FIELD_NAME
ssh_key_path:           master_ssh_key_path
ignore_docker_version:  ignore_docker_version