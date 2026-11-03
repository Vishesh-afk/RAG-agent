# RAG Agent DevOps Project Memory

Last updated: 2026-11-03

Use this file as the project continuity note before making recommendations or changes. The user's current target plan below supersedes older learning notes in `DEVOPS-HANDS-ON.md` where they conflict. Teach one practical checkpoint at a time in plain language. Prefer AWS/GitLab web consoles for cloud setup and give exact WSL commands only where a console cannot do the job. Explain why a resource is needed, avoid surprise AWS costs, and include a clear verification step. Do not read, print, commit, or expose `.env` or other secret values.

## Target outcome

Build an end-to-end, automated CI/CD and GitOps deployment for the three-tier RAG Agent (frontend, FastAPI backend, PostgreSQL/pgvector) using:

- GitLab for application source control and CI/CD.
- SonarQube analysis with a Quality Gate that fails the pipeline when the gate fails.
- Docker builds and versioned images in a private DockerHub repository.
- A separate GitOps repository containing deployment configuration and image tags.
- Kubernetes on the existing EKS cluster, with ArgoCD automatically syncing and self-healing from Git.
- Prometheus and Grafana for application/cluster monitoring, dashboards, and alerts.

Acceptance challenges: Quality Gate failure blocks release; no manual `kubectl apply` for normal deployments; ArgoCD repairs deliberate cluster drift; probes recover unhealthy containers; HPA scales; a failed release can be rolled back; Grafana shows dashboards and actionable alerts.

## Master roadmap and status

| Phase | Area | Status / outcome |
|---|---|---|
| 1 | Application and Docker | Completed baseline. Frontend and backend Dockerfiles and Compose stack exist. |
| 2 | AWS infrastructure | Partially complete. Existing EKS/VPC/node/storage foundation is in use. Avoid rebuilding it. |
| 3 | CI/CD | In progress. Existing Jenkins-to-ECR pipeline is a learning baseline; the target pipeline is GitLab CI, SonarQube, DockerHub, and GitOps tag update. |
| 4 | Kubernetes deployment | Next target phase. EKS currently runs the app manually; standardize manifests and let ArgoCD deploy them from Git. |
| 5 | GitOps | Planned: separate GitOps repo, ArgoCD auto-sync and self-heal. |
| 6 | Monitoring and logging | Planned: Prometheus, Grafana, dashboards, and alerts. Fluent Bit/log collection can be added when scoped. |
| 7 | Autoscaling | Planned: HPA first; verify metrics support. Karpenter later, only if needed and after cost review. |
| 8 | AI observability | Planned: Arize Phoenix. |
| 9 | Production readiness | Planned: security, reliability, rollout/rollback, cost, and operational review. |

## Repository baseline (inspected read-only on 2026-11-03)

- Current local repo is the app project. GitHub remains as remote `origin` (`https://github.com/Vishesh-afk/RAG-agent.git`); GitLab app repo is remote `gitlab` (`https://gitlab.com/visheshchourasia143/rag-agent.git`).
- On 2026-11-03, local `main` was safely merged with GitLab's auto-generated starter README commit, keeping the app's existing README. The merge commit was pushed successfully, and local `main` now tracks `gitlab/main`.
- App files include root `Dockerfile` (Python 3.12), `frontend/Dockerfile` (Node 22 build, Nginx runtime), `docker-compose.yml`, and `docker-compose.override.yml`.
- Compose runs frontend, FastAPI API, and PostgreSQL with pgvector. Local Postgres uses a learning default if env values are absent; do not carry that default into a shared deployment.
- Python tests exist under `tests/`; `pyproject.toml` configures pytest. `frontend/package.json` has a production build script but no frontend test script.
- At inspection there was no `.gitlab-ci.yml`, SonarQube config, Kubernetes manifest/Helm chart, or ArgoCD config in the repo.
- `frontend/src/lib/api.ts` uses `VITE_API_URL` with a localhost fallback. Check how production frontend reaches the backend before publishing an Ingress or choosing API paths.
- `.env` exists locally and is ignored by Git. Do not inspect or commit it. `docker-compose.yml` references it for local configuration.
- `DEVOPS-HANDS-ON.md` contains an older Bitbucket/Jenkins/Snyk roadmap and should be reconciled with this file when convenient; this file is the current source of truth.

## Existing local work to preserve

At the last `git status` inspection, the branch was `main` tracking `gitlab/main`, with:

- Modified tracked files: `agent/prompts.py`, `ingestion/extract_files.py`.
- Untracked directory: `.vscode/`.

The diffs currently add document-title handling to PDF extraction and improve title use in agent instructions. `.vscode/settings.json` is the only file in the untracked VS Code folder. Preserve these changes. Do not discard, overwrite, stage, or commit them without checking their intent. Keep `.env` and secrets out of GitLab and the GitOps repo. No tests were run during the read-only inventory.

## Existing AWS/EKS state

- Region: `us-east-2` (Ohio); existing cluster: `northstar-dev-eks` (Kubernetes 1.37 at last report).
- Namespace: `northstar-rag-dev`.
- EKS has two `t3.small` worker nodes in the active node group. A separate failed node-group attempt is not needed for current work.
- Backend Deployment/Service (`northstar-api` / `api`), frontend Deployment/Service (`northstar-frontend`), and PostgreSQL StatefulSet (`postgres`) are running. PostgreSQL uses an 8 GiB bound PVC on `northstar-gp3-retain`; retain this data path unless the user chooses otherwise.
- API `/health` and frontend were previously checked successfully through port-forward. ClusterIP services are private; port-forward is temporary/local access.
- AWS Load Balancer Controller is installed in `kube-system` with one ready replica, using EKS Pod Identity. Public subnet tags were added. No Ingress or ALB exists. Public access is optional and deferred because an ALB/public IPv4 incur ongoing charges.
- Do not create an ALB/Ingress without first stating expected costs and getting clear user approval.
- No RDS database exists; PostgreSQL currently runs in EKS. Do not migrate it or create RDS without discussion of architecture and cost.
- AWS CloudShell was unavailable due to account verification; user works from Ubuntu on WSL2. App repo path there is `/mnt/c/Users/VisheshChourasia/OneDrive - Info Origin Technologies Pvt Ltd/Desktop/rag agent`.
- Never ask the user to print AWS credentials, API keys, `.env`, or Kubernetes Secret values.

## Jenkins pipeline evidence

The user supplied a successful Jenkins build log for job `northstar-ragagent-ecr-pipeline`. It checked out the GitHub `main` branch, built backend and frontend images tagged `:1`, authenticated to ECR, and pushed both images. It ended `Finished: SUCCESS`.

That run did **not** include tests, SonarQube, DockerHub, a GitOps tag commit, or EKS deployment. Treat it as a working CI/image-publishing baseline, not completion of the new target. The log showed Docker credentials saved unencrypted in Jenkins' Docker config; plan to avoid persistent plaintext Docker auth in the target pipeline. The Jenkins EC2 security group was adjusted to allow port 8080 from the user's current IP; whether the Jenkins UI is now reachable was not confirmed.

## Recommended execution sequence

1. **Protect and inspect current work.** Review the two modified files and `.vscode/` purpose; preserve changes. Confirm `.env` is ignored without reading it.
2. **Set up GitLab repositories.** Create a GitLab application repo and a separate GitOps repo. Keep GitHub history/origin until migration is deliberate. Do not push local secrets.
3. **Define CI prerequisites.** Decide where SonarQube runs and confirm GitLab runner capabilities. Add safe unit/build checks, Sonar analysis, and a Quality Gate failure condition.
4. **Publish images.** Build commit-based/release-versioned frontend and backend images; push to private DockerHub using protected GitLab CI variables, never echo credentials.
5. **Prepare Kubernetes desired state.** Create/organize manifests for frontend, backend, and the existing PostgreSQL data path. Add ConfigMaps, Secret handling, probes, resource requests/limits, rolling update settings, Services, and HPA. Validate metrics-server support before HPA. Do not commit plaintext Kubernetes Secret data; choose an appropriate secret delivery pattern before enabling ArgoCD.
6. **Automate GitOps promotion.** After image push and gate success, update the image tag in the separate GitOps repo. Use a dedicated token with minimum access.
7. **Install/configure ArgoCD.** Watch the GitOps repo and namespace, enable auto-sync/self-heal, and verify that a Git change deploys without manual `kubectl apply`. Define rollback as a Git revert or another explicit, tested release strategy; do not assume ArgoCD automatically rolls back every unhealthy release.
8. **Observe and alert.** Install Prometheus/Grafana in a cost-aware way; add cluster and application dashboards, alerts for pod failures, high CPU/memory, and deployment health. Add Fluent Bit/log collection if required.
9. **Run acceptance exercises.** Deliberately fail Quality Gate, induce Git drift, break a health check, trigger HPA, roll back a bad release, and verify dashboards/alerts. Restore healthy state after each exercise.
10. **Production readiness.** Review IAM/RBAC, image/dependency scanning, secret rotation, backup/restore for PostgreSQL PVC, ingress/TLS/domain costs if public access is wanted, capacity, and operational documentation.

## Immediate next checkpoint

The application repo is now pushed to GitLab. The separate GitOps project URL provided by the user is `https://gitlab.com/visheshchourasia143/rag-agent-gitops.git`; its contents/initialization have not been inspected or populated. Next, preserve and intentionally handle the current local modifications, then prepare the first GitLab CI stages using project variables for external service credentials. Do not push local secrets. Avoid making a new Jenkins job; the existing job is already known and its limitations are documented above.
