## To use locally:

### Setup:
- create .ssh/ in main validations/ directory, download aws.pem cert for tests
- rke and kubectl need to be in your path
- pip install requirements.txt (recommend using virtualenv before this step)
- export following variables:

```
OS_VERSION=[ubuntu-16.04|rhel-7.4]
DOCKER_VERSION=[latest|17.03|1.13.1|1.12.6]
CLOUD_PROVIDER=AWS
AWS_SSH_KEY_NAME=aws_cert.pem
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

### Run:
    pytest -s rke_tests/


## To run locally in container:
- save ssh pem file from AWS in validations/.ssh
- export following variables:

```
OS_VERSION=[ubuntu-16.04|rhel-7.4]
DOCKER_VERSION=[latest|17.03|1.13.1|1.12.6]
KUBECTL_VERSION=
RKE_VERSION=
CLOUD_PROVIDER=AWS
AWS_SSH_KEY_NAME=aws_cert.pem
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```
- run scripts/rke/configure.sh
- run scripts/rke/build.sh
- run docker run --rm -v ~/path/to/rancher-validation:/src/rancher-validation rancher-validation-tests -c pytest -s rke_tests/

