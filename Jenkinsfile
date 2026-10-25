pipeline {
  agent any
  parameters {
    string(name: 'EC2_HOST', defaultValue: '', description: 'Public EC2 IP for deployment; leave blank to skip deploy')
  }
  environment {
    IMAGE_PREFIX = 'ghcr.io/abdelaziz-adel/smart-inventory'
  }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Test') {
      steps {
        sh 'POSTGRES_PASSWORD=ci_test_password docker compose build'
        sh 'POSTGRES_PASSWORD=ci_test_password docker compose run --rm -e DATABASE_URL=sqlite:////tmp/test.db backend pytest -q'
        sh 'POSTGRES_PASSWORD=ci_test_password docker compose run --rm alerts python -m compileall .'
      }
    }
    stage('Build & Push') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'ghcr-creds', usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_TOKEN')]) {
          sh '''
            set -eu
            echo "$REGISTRY_TOKEN" | docker login ghcr.io -u "$REGISTRY_USER" --password-stdin
            docker build -t "$IMAGE_PREFIX-backend:latest" backend
            docker build -t "$IMAGE_PREFIX-alerts:latest" alerts
            docker build -t "$IMAGE_PREFIX-frontend:latest" -f frontend/Dockerfile .
            docker push "$IMAGE_PREFIX-backend:latest"
            docker push "$IMAGE_PREFIX-alerts:latest"
            docker push "$IMAGE_PREFIX-frontend:latest"
            docker logout ghcr.io
          '''
        }
      }
    }
    stage('Deploy') {
      when { expression { return params.EC2_HOST?.trim() } }
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'ec2-ssh', keyFileVariable: 'EC2_KEY', usernameVariable: 'EC2_USER')]) {
          sh '''
            set -eu
            ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" \
              'sudo k3s kubectl -n inventory rollout restart deployment/backend deployment/alerts deployment/frontend && sudo k3s kubectl -n inventory rollout status deployment/backend --timeout=180s && sudo k3s kubectl -n inventory rollout status deployment/alerts --timeout=180s && sudo k3s kubectl -n inventory rollout status deployment/frontend --timeout=180s'
          '''
        }
      }
    }
  }
}
