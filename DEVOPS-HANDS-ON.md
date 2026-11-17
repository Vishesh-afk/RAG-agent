# DevOps hands-on setup

## Target flow

GitHub application repository → Jenkins CI → Docker Hub images → separate GitHub GitOps repository → Argo CD on local Minikube.

Application source and the Jenkins pipeline stay in this repository. Kubernetes manifests stay in the separate [rag-agent-gitops repository](https://github.com/Vishesh-afk/rag-agent-gitops).

## Local runtime secret

Keep runtime values in the ignored `.env` file in the application repository. Do not commit or print it.

Create the namespace and Kubernetes Secret:

```sh
kubectl create namespace rag-agent --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic rag-agent-runtime --from-env-file=.env --namespace rag-agent
```

The `.env` file needs `DB_USER`, `DB_PASSWORD`, and `OPENAI_API_KEY`. Optional model settings can also be provided. The Secret is created directly in the local Minikube cluster.

If the Secret already exists, update it with:

```sh
kubectl create secret generic rag-agent-runtime --from-env-file=.env --namespace rag-agent --dry-run=client -o yaml | kubectl apply -f -
```

The backend image is private. Create a Docker Hub pull Secret named `dockerhub-auth` in namespace `rag-agent`, then ensure the workload can use it.

## Jenkins setup

Create a Multibranch Pipeline for this GitHub repository and configure these Jenkins credentials:

- `dockerhub`: Docker Hub username and access token.
- `github-gitops-deploy-key`: SSH private key with write access to the GitOps repository.

The Jenkinsfile builds the backend and frontend, publishes commit-SHA and `latest` tags to Docker Hub, and commits the SHA tags to the Minikube overlay in the GitOps repository.

## Argo CD and Minikube

Install Minikube and Argo CD, then apply the Argo CD Application from the GitOps repository:

```sh
kubectl apply -f clusters/minikube/apps/rag-agent.yaml
```

Sync the application in Argo CD. Confirm the API, frontend, and PostgreSQL workloads become healthy in namespace `rag-agent`.

## Deliberately out of scope

SonarQube and other unused CI integrations remain disabled. Monitoring artifacts are present in this repository, but live monitoring on Minikube has not been verified.
