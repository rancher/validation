

node {
  wrap([$class: 'AnsiColorBuildWrapper', 'colorMapName': 'XTerm', 'defaultFg': 2, 'defaultBg':1]) {
    checkout scm

    stage('Configure and Build') {
      sh "./scripts/rke/configure.sh"
      sh "mkdir -p .ssh && echo \"${AWS_SSH_PEM_KEY}\" > .ssh/${AWS_SSH_KEY_NAME} && chmod 400 .ssh/*"
      sh "./scripts/rke/build.sh"
    }

    stage('Run Validation Tests') {
      sh "docker run --rm -v jenkins_home:/var/jenkins_home --env-file .env " +
         "rancher-validation-tests /bin/bash -c \'pytest -s rke_tests/\'"
    }

  }
}