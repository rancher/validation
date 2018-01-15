

node {
  wrap([$class: 'AnsiColorBuildWrapper', 'colorMapName': 'XTerm', 'defaultFg': 2, 'defaultBg':1]) {
    checkout scm

    stage('Configure and Build') {
      sh "./scripts/rke/configure.sh"
      sh "./scripts/rke/build.sh"
    }

    stage('Run Validation Tests') {
      sh "docker run --rm -v jenkins_home:/var/jenkins_home --env .env " +
         "-e WORKSPACE_DIR=\"$(pwd)\" rancher-validation-tests " +
         "/bin/bash -c \'cd \"$(pwd)\" && pytest -s\'"
    }

  }
}