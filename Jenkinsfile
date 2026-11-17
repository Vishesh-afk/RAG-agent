pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    BACKEND_IMAGE = 'vishesh11/ragagent-backend'
    FRONTEND_IMAGE = 'vishesh11/ragagent-frontend'
    GITOPS_REPO = 'git@github.com:Vishesh-afk/rag-agent-gitops.git'
    GITOPS_PATH = 'apps/rag-agent/overlays/minikube'
  }

  stages {
    stage('Validate') {
      steps {
        sh 'python -m compileall -q agent ingestion'
        dir('frontend') {
          sh 'npm ci && npm run build'
        }
      }
    }

    stage('Build and publish images') {
      when { branch 'main' }
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
      when { branch 'main' }
      steps {
        sshagent(credentials: ['github-gitops-deploy-key']) {
          dir('gitops') {
            deleteDir()
            sh '''
              set -eu
              git clone "$GITOPS_REPO" .
              python - "$GIT_COMMIT" "$GITOPS_PATH" <<'PY'
import pathlib, re, sys
tag, folder = sys.argv[1:]
for name, image in (("api-deployment.yaml", "vishesh11/ragagent-backend"),
                    ("frontend-deployment.yaml", "vishesh11/ragagent-frontend")):
    path = pathlib.Path(folder) / name
    text = path.read_text()
    updated, count = re.subn(rf'(?m)^(\s*image:\s*{re.escape(image)}:)[^\s]+', rf'\g<1>{tag}', text)
    if count != 1:
        raise SystemExit(f"Expected one image reference for {image} in {path}, found {count}")
    path.write_text(updated)
            PY
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

