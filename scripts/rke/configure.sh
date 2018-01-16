#!/bin/bash

set -eu

DEBUG="${DEBUG:-false}"

env | egrep '^(RANCHER_|AWS_|DEBUG|DOCKER_|CLOUD_|KUBECTL_|BUILD_NUMBER).*\=.+' | sort > .env

if [ "false" != "${DEBUG}" ]; then
    cat .env
fi
