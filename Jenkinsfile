pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    BACKEND_IMAGE = 'vishesh11/ragagent-backend'
    FRONTEND_IMAGE = 'vishesh11/ragagent-frontend'
    GITOPS_REPO = 'https://github.com/Vishesh-afk/rag-agent-gitops.git'
    GITOPS_PATH = 'apps/rag-agent/overlays/minikube'
  }

  stages {

    
    stage('Build and publish images') {
      when {
        expression {
          env.BRANCH_NAME == 'main' || env.GIT_BRANCH == 'main' || env.GIT_BRANCH == 'origin/main'
        }
      }
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_TOKEN')]) {
          sh '''
            set +x
            printf '%s' "$DOCKER_TOKEN" | docker login --username "$DOCKER_USER" --password-stdin
            docker build --pull -t "$BACKEND_IMAGE:$GIT_COMMIT" -t "$BACKEND_IMAGE:latest" -f Dockerfile .
            docker build --pull -t "$FRONTEND_IMAGE:$GIT_COMMIT" -t "$FRONTEND_IMAGE:latest" frontend
            docker push "$BACKEND_IMAGE:$GIT_COMMIT"
            docker push "$FRONTEND_IMAGE:$GIT_COMMIT"
            docker push "$BACKEND_IMAGE:latest"
            docker push "$FRONTEND_IMAGE:latest"
            docker logout
          '''
        }
      }
    }

    stage('Promote GitOps manifests') {
      when {
        expression {
          env.BRANCH_NAME == 'main' || env.GIT_BRANCH == 'main' || env.GIT_BRANCH == 'origin/main'
        }
      }
      steps {
        withCredentials([gitUsernamePassword(credentialsId: 'github-gitops-write-token', gitToolName: 'Default')]) {
          dir('gitops') {
            deleteDir()
            sh '''
              set -eu
              git clone "$GITOPS_REPO" .
              test "$(grep -Ec '^[[:space:]]*image:[[:space:]]*vishesh11/ragagent-backend:' "$GITOPS_PATH/api-deployment.yaml")" -eq 1
              test "$(grep -Ec '^[[:space:]]*image:[[:space:]]*vishesh11/ragagent-frontend:' "$GITOPS_PATH/frontend-deployment.yaml")" -eq 1
              sed -i -E "s#(^[[:space:]]*image:[[:space:]]*vishesh11/ragagent-backend:).*#\\1${GIT_COMMIT}#" "$GITOPS_PATH/api-deployment.yaml"
              sed -i -E "s#(^[[:space:]]*image:[[:space:]]*vishesh11/ragagent-frontend:).*#\\1${GIT_COMMIT}#" "$GITOPS_PATH/frontend-deployment.yaml"
              git config user.name 'Jenkins CI'
              git config user.email 'jenkins@users.noreply.github.com'
              git add "$GITOPS_PATH/api-deployment.yaml" "$GITOPS_PATH/frontend-deployment.yaml"
              if ! git diff --cached --quiet; then
                git commit -m "Deploy ${GIT_COMMIT} to Minikube"
                git push origin HEAD:main
              fi
            '''
          }
        }
      }
    }
  }

  post {
    always {
      sh 'docker logout >/dev/null 2>&1 || true'
      cleanWs()
    }
  }
}

