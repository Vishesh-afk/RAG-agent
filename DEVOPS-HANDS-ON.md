# DevOps hands-on setup

Target learning path: GitHub application repository → Jenkins CI → Docker Hub images → separate GitHub GitOps repository → Argo CD deployment to local Minikube. This application repository contains source and the Jenkins pipeline; Kubernetes desired state belongs in `rag-agent-gitops`. AWS Secrets Manager holds runtime credentials. Grafana/Prometheus artifacts exist, but cluster monitoring must be checked against Minikube before calling it live.

## Start locally

1. Install and start Docker Desktop.
2. Copy `.env.example` to `.env` and add an OpenAI API key when you are ready to use chat or embeddings. The checked-in `.env.example` has no key.
3. From this directory, run:

   ```sh
   docker compose up --build
   ```

4. Open the React app at <http://localhost:3000>. API docs are at <http://localhost:8058/docs>.

The database is published on port `6543` and its data persists in the `postgres_data` volume. User-uploaded PDFs persist in `documents_data`. The default stack does not start the older Streamlit interface; start it separately with `docker compose --profile streamlit up --build` if you want to compare it.

Stop the stack with `docker compose down`. To remove the local database and uploaded-document volumes too, run `docker compose down -v`.

## Data handling

The repository includes PDFs under `documents/`, including a resume. They are excluded from Docker build contexts and are not loaded into the database automatically. Upload only documents you choose through the app; ingestion sends document text to the configured embedding provider.

## Current local configuration notes

- The API image uses Python 3.12 to match `pyproject.toml`.
- `.env` is ignored by Git. Keep real API keys there and never commit them.
- The Compose database password is a local-learning default. Replace it with managed secrets for shared or cloud deployments.

## Local Kubernetes delivery

### Jenkins prerequisites

- Configure a Multibranch Pipeline to use this GitHub repository's `Jenkinsfile`, with a GitHub webhook for push events.
- Jenkins agent needs Python 3.12, Node.js 22/npm, Docker Engine access, Git, and the Jenkins Docker Pipeline, Credentials Binding, SSH Agent, and Workspace Cleanup plugins.
- Add Jenkins credential `dockerhub` as a username/password credential containing the Docker Hub username and access token.
- Add `github-gitops-deploy-key` as an SSH private key with write access to the separate `rag-agent-gitops` repository.
- Run a successful job on `main`; feature branches only run validation. Jenkins publishes SHA and `latest` tags for both images, then commits the SHA tags to `apps/rag-agent/overlays/minikube` in the GitOps repository.

### Minikube, Argo CD, and external secrets

The public `rag-agent-gitops` repository keeps manifests under `apps/rag-agent/overlays/minikube/` and the Argo CD Application under `clusters/minikube/apps/`. Install Argo CD and the External Secrets Operator (ESO) in Minikube before syncing the application. Apply the Application resource once to register it; after that, Argo CD owns application resources. The repo is public, so Argo CD does not need a GitHub read credential.

Create AWS Secrets Manager secret `rag-agent/minikube/runtime` as a JSON object with `DB_USER`, `DB_PASSWORD`, `OPENAI_API_KEY`, `LLM_CHOICE`, and `EMBEDDING_MODEL`. Do not put these values in Git, Jenkins parameters, or chat. The store currently targets `us-east-2`, matching the project's last known AWS region; verify the secret is in that region before Argo sync. ESO reads it and creates the Kubernetes Secret `rag-agent-runtime` consumed by PostgreSQL and the API. On first startup, PostgreSQL initializes the user/password from this secret; changing Secrets Manager later does not rotate the password in an existing data directory automatically.

Minikube does not have an AWS IAM role by default. For this local learning setup, create a dedicated AWS identity with read-only access to only `rag-agent/minikube/runtime`, then create the ESO bootstrap Secret `aws-secrets-manager-auth` in namespace `rag-agent` using its access key ID and secret access key. Keep those values out of shell history and source control; rotate/revoke the identity when no longer needed. This bootstrap credential is separate from the application credentials held in Secrets Manager. For EKS later, replace it with workload identity instead of carrying static keys forward.

The API image is private and the deployment references `dockerhub-auth` in namespace `rag-agent`. Create that image pull secret locally before the first sync. The frontend is served through its NodePort service; use `minikube service frontend -n rag-agent --url` to open it. PostgreSQL uses a local 8 GiB PVC, which is not a backup.

### Disabled pipeline

GitHub Actions, SonarQube, and GitLab CI are not part of this path. CI runs in Jenkins; CD runs through Argo CD from the separate GitOps repository.

## Monitoring handoff

- The user verified the RAG API scrape and imported an API dashboard into Grafana; Prometheus returned request-rate data.
- Import `ops/phase6/grafana/rag-agent-application-cluster-dashboard.json` through Grafana's dashboard importer and select the Prometheus data source.
- `ops/phase6/grafana/northstar-kubernetes-alerts.json` is a separate Grafana alert-rule provisioning file. Replace `PROMETHEUS_DATASOURCE_UID`, mount it under `/etc/grafana/provisioning/alerting/`, then restart Grafana. Set up a contact point/policy separately if notifications are wanted.
- Kubernetes workload panels and rules need Prometheus to scrape kube-state-metrics and kubelet/cAdvisor for `northstar-rag-dev`; local Prometheus screenshots only prove app, Node Exporter, and Prometheus targets. Don't claim cluster metrics are live until checked.
- The API source includes `/metrics` instrumentation. Verify the running image and Prometheus target against Minikube before relying on application panels.
- Preserve the user's WSL practice files: `/home/vishesh/monitoring/prometheus/prometheus.yml`, `/home/vishesh/fluentbit-lab/docker-compose.yml`, and `/home/vishesh/fluentbit-lab/loki-config.yaml`.

## Learning path

1. Understand and run the application locally.
2. Container and configuration hardening.
3. Jenkins CI and Docker Hub image publishing.
4. Argo CD GitOps deployment to Minikube.
5. AWS Secrets Manager integration and local bootstrap identity.
6. Verify Prometheus/Grafana Kubernetes metrics and alerts.
7. HPA and AI observability after a healthy baseline.
8. Production readiness and failure exercises.

