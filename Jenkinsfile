

node {
  wrap([$class: 'AnsiColorBuildWrapper', 'colorMapName': 'XTerm', 'defaultFg': 2, 'defaultBg':1]) {
    checkout scm

    stage('Configure and Build') {
      sh "./scripts/rke/configure.sh"
      sh "ls .ssh"
      sh "mkdir -p .ssh && echo -e \"${AWS_SSH_PEM_KEY}\" > .ssh/${AWS_SSH_KEY_NAME}"
      sh "cat .ssh/${AWS_SSH_KEY_NAME}"
      sh "./scripts/rke/build.sh"

    }

    stage('Run Validation Tests') {
      sh "docker run --rm -v jenkins_home:/var/jenkins_home --env-file .env " +
         "rancher-validation-tests /bin/bash -c \'pytest -s rke_tests/\'"
    }

  }
}