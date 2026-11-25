pipeline {
  agent any

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    disableConcurrentBuilds()
    timeout(time: 30, unit: 'MINUTES')
  }

  environment {
    IMAGE_NAME = 'bugsentinel-ai'
    IMAGE_TAG = "${BUILD_NUMBER}"
    PYTHONUNBUFFERED = '1'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          if (isUnix()) {
            sh 'git rev-parse --short HEAD'
          } else {
            bat 'git rev-parse --short HEAD'
          }
        }
      }
    }

    stage('Backend: install and test') {
      steps {
        script {
          if (isUnix()) {
            sh '''#!/bin/sh
              python3 -m venv .jenkins-venv
              . .jenkins-venv/bin/activate
              python -m pip install --upgrade pip
              python -m pip install -r requirements.txt
              python -m pytest tests/test_analyzer.py tests/test_api.py \\
                --cov=app --cov-report=xml --junitxml=test-results.xml
            '''
          } else {
            bat '''@echo on
              py -3 -m venv .jenkins-venv
              call .jenkins-venv\\Scripts\\activate.bat
              python -m pip install --upgrade pip
              python -m pip install -r requirements.txt
              python -m pytest tests/test_analyzer.py tests/test_api.py --cov=app --cov-report=xml --junitxml=test-results.xml
            '''
          }
        }
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'test-results.xml'
        }
      }
    }

    stage('Frontend: verify') {
      steps {
        dir('frontend') {
          script {
            if (isUnix()) {
              sh 'npm ci && npm run typecheck && npm run build'
            } else {
              bat 'call npm ci && call npm run typecheck && call npm run build'
            }
          }
        }
      }
    }

    stage('Docker Compose: validate') {
      steps {
        script {
          if (isUnix()) {
            sh '''#!/bin/sh
              printf 'JWT_SECRET=ci-placeholder-not-a-real-secret\nPOSTGRES_PASSWORD=ci-placeholder\n' > .env
              docker compose config --quiet
              result=$?
              rm -f .env
              exit $result
            '''
          } else {
            bat '''@echo off
              (
                echo JWT_SECRET=ci-placeholder-not-a-real-secret
                echo POSTGRES_PASSWORD=ci-placeholder
              ) > .env
              docker compose config --quiet
              set result=%ERRORLEVEL%
              del /q .env
              exit /b %result%
            '''
          }
        }
      }
    }

    stage('Docker: build API image') {
      steps {
        script {
          if (isUnix()) {
            sh 'docker build --pull -t $IMAGE_NAME:$IMAGE_TAG .'
          } else {
            bat 'docker build --pull -t %IMAGE_NAME%:%IMAGE_TAG% .'
          }
        }
      }
    }

    stage('Security: container scan') {
      steps {
        script {
          if (isUnix()) {
            sh '''#!/bin/sh
              docker save -o bugsentinel-image.tar $IMAGE_NAME:$IMAGE_TAG
              docker run --rm \\
                -v "$PWD:/workspace" \\
                aquasec/trivy:0.58.1 image \\
                --input /workspace/bugsentinel-image.tar \\
                --severity HIGH,CRITICAL --exit-code 0 --no-progress
              result=$?
              rm -f bugsentinel-image.tar
              exit $result
            '''
          } else {
            bat '''@echo off
              docker save -o bugsentinel-image.tar %IMAGE_NAME%:%IMAGE_TAG%
              if errorlevel 1 exit /b 1
              docker run --rm -v "%CD%:/workspace" aquasec/trivy:0.58.1 image --input /workspace/bugsentinel-image.tar --severity HIGH,CRITICAL --exit-code 0 --no-progress
              set result=%ERRORLEVEL%
              del /q bugsentinel-image.tar
              exit /b %result%
            '''
          }
        }
      }
    }

    stage('Branch policy') {
      steps {
        script {
          if (env.BRANCH_NAME == 'zk') {
            echo 'Integration branch validated. Open a pull request from zk to staging when ready.'
          } else if (env.BRANCH_NAME == 'staging') {
            echo 'Staging branch validated. Open a reviewed pull request from staging to master for release.'
          } else if (env.BRANCH_NAME == 'master') {
            echo 'Main branch release candidate validated. Cloud deployment is a later phase.'
          } else {
            echo "Feature branch ${env.BRANCH_NAME ?: 'unknown'} validated; merge through zk."
          }
        }
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'coverage.xml,test-results.xml', allowEmptyArchive: true
      script {
        if (isUnix()) {
          sh 'rm -rf .jenkins-venv || true'
        } else {
          bat 'if exist .jenkins-venv rmdir /s /q .jenkins-venv'
        }
      }
    }
    success {
      echo 'CI pipeline completed successfully.'
    }
  }
}
