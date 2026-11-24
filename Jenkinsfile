pipeline {
  agent any
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Unit tests') { steps { sh 'python -m pip install -r requirements.txt && pytest tests/test_analyzer.py tests/test_api.py' } }
    stage('Frontend build') { steps { sh 'cd frontend && npm install && npm run build' } }
    stage('SAST') { steps { sh 'docker run --rm -v $PWD:/src returntocorp/semgrep semgrep --config auto /src || true' } }
    stage('Build image') { steps { sh 'docker build -t bugsentinel-ai:${BUILD_NUMBER} .' } }
    stage('Container scan') { steps { sh 'trivy image --exit-code 0 bugsentinel-ai:${BUILD_NUMBER} || true' } }
    stage('Deploy') { when { branch 'main' }; steps { sh 'kubectl apply -f k8s/' } }
  }
}
