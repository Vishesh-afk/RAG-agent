# RAG Agent DevOps Project Memory

Last updated: 2026-11-05
Last updated: 2026-11-05

Use this file as the project continuity note before making recommendations or changes. It reflects the local repository and the recent Codex project chats. Prefer the newest verified state over older roadmap notes. Teach one practical checkpoint at a time in plain language, explain AWS cost implications before cost-incurring changes, and never read, print, commit, or expose `.env` or other secret values.
Use this file as the project continuity note before making recommendations or changes. It reflects the local repository and the recent Codex project chats. Prefer the newest verified state over older roadmap notes. Teach one practical checkpoint at a time in plain language, explain AWS cost implications before cost-incurring changes, and never read, print, commit, or expose `.env` or other secret values.

## Target outcome

Build and demonstrate an end-to-end DevOps flow for the RAG Agent (React frontend, FastAPI backend, PostgreSQL/pgvector): GitHub Actions CI, SonarQube Quality Gate, DockerHub image publishing, GitOps manifests in a separate GitLab repo, ArgoCD deployment to EKS, then monitoring, autoscaling, AI observability, and production-readiness exercises.

The user has emphasized that work they believe is complete should be checked against prior project chats before being marked remaining. Keep this file current after meaningful milestones and use it to resume work.
Build and demonstrate an end-to-end DevOps flow for the RAG Agent (React frontend, FastAPI backend, PostgreSQL/pgvector): GitHub Actions CI, SonarQube Quality Gate, DockerHub image publishing, GitOps manifests in a separate GitLab repo, ArgoCD deployment to EKS, then monitoring, autoscaling, AI observability, and production-readiness exercises.

The user has emphasized that work they believe is complete should be checked against prior project chats before being marked remaining. Keep this file current after meaningful milestones and use it to resume work.

## Current roadmap
## Current roadmap

| Phase | Area | Status / last known evidence |
| Phase | Area | Status / last known evidence |
|---|---|---|
| 1 | Application and Docker | Baseline complete: React frontend, FastAPI backend, PostgreSQL/pgvector, Dockerfiles and Compose stack. |
| 2 | AWS infrastructure | Partly complete. Existing EKS/VPC was used. **User reports the EKS worker node group has now been deleted** to reduce costs. The cluster control plane and retained EBS/storage or other AWS resources may still incur charges. Do not recreate workers until the final deployment checkpoint. |
| 3 | CI and image publishing | Core pipeline is implemented. Run `715684d` passed syntax, frontend build and SonarQube Quality Gate, then pushed both images. Direct GitLab writes to protected `main` previously failed with HTTP 403. The current local workflow now attempts to commit image tags directly to GitLab `main`; the token bot must be allowed to push to that protected branch, and a successful run is still needed to verify promotion. |
| 4 | Kubernetes deployment | App has been deployed on EKS and accessed using port-forward in prior chats. GitOps manifests were applied through ArgoCD. Latest reported rollout was not healthy: backend image extraction failed with `no space left on device`, and the node reported ephemeral-storage, memory, and pod-capacity pressure. Frontend was healthy; PostgreSQL readiness had timed out, though its 8 GiB PVC remained bound. Recheck live state. |
| 5 | GitOps / ArgoCD | GitLab GitOps repo and dev manifests are in place; `kubectl kustomize` successfully rendered the dev overlay during this turn. ArgoCD is local on Docker Desktop, connected to EKS with namespace-scoped access, and Application `northstar-rag-dev` uses **manual sync**. GitHub Actions has the GitLab token. A previous direct-to-main promotion was blocked by HTTP 403; the current workflow retries direct commits, pending confirmation that the token bot is allowed to push to protected `main`. Argo still requires manual Sync. Auto-sync/self-heal is not enabled/verified. |
| 6 | Monitoring and logging | Preparation added locally in `ops/phase6/`: kube-prometheus-stack values, API `/metrics` instrumentation, ServiceMonitor template, app/cluster alert rules for pod failures, CPU, memory, deployment availability and PVC space, Fluent Bit to CloudWatch values, and install/verification guidance. Not installed or live-verified; API Service labels/port must be matched to the GitOps manifests, and worker nodes, AWS costs, IRSA and an Alertmanager notification receiver remain prerequisites. |
| 7 | Autoscaling | Not yet confirmed. Configure and test HPA only after EKS metrics support and a healthy baseline are confirmed. Karpenter is optional and deferred pending cost review. |
| 8 | AI observability | Not yet integrated. Arize Phoenix (and LiteLLM in an earlier learning plan) were discussed; confirm scope before implementation. |
| 9 | Production readiness | Remaining: acceptance exercises, access/secrets review, backup/restore, reliability, rollout/rollback, cost review, and operational documentation. |

## Immediate resume point and sequencing

The user reports deleting the EKS worker node group to reduce cost. **Keep workers absent while preparing the remaining components; create a worker node group only as the final step before deploying/testing the application on Kubernetes.** This is the user's chosen order.

1. **Prepare and verify what can be done without worker nodes:** review the GitHub Actions workflow and latest run; decide/implement CI-to-GitOps image-tag promotion; validate the GitOps manifests and secret delivery references; prepare monitoring, autoscaling and AI observability configuration in source control where practical. Phase 6 preparation is in `ops/phase6/`; avoid applying workloads to EKS while it has no workers.
2. **Recheck AWS billing and cluster state before cloud mutations.** Worker deletion should stop worker EC2 compute charges, but does not stop EKS control-plane charges or charges for retained EBS volumes and other resources. Do not delete the cluster or PostgreSQL volume unless the user explicitly directs it.
3. Before the final deployment stage, resolve the previous worker ephemeral-storage/image-size and capacity issue. The backend image extraction previously failed with `no space left on device`; a large OpenCV layer and retained `uv` cache were identified as possible contributors. Choose appropriate worker instance/disk capacity and communicate costs before creating the node group.
4. **Final infrastructure checkpoint:** recreate the EKS worker node group, verify nodes become Ready, then deploy/sync through ArgoCD and verify PostgreSQL, API and frontend readiness plus Argo Healthy status. Last reported frontend was healthy; backend replacement pod was not ready and PostgreSQL readiness had timed out.
5. Keep Argo manual sync as the safety gate until manifests and deployment are validated. Do not enable auto-sync/pruning without reviewing the diff and confirming database storage is protected.
6. Push the revised app-repo workflow; the GitLab access token is configured as `GITLAB_GITOPS_TOKEN`. Verify the token bot is permitted to push to GitLab `main`, then confirm a passing release directly commits both GitOps image tags. Review Argo's diff and manually Sync after workers are recreated and the cluster is healthy.

Useful WSL status command (read-only):

```bash
kubectl get nodes
kubectl get pods,services,pvc -n northstar-rag-dev
```

## Repository and CI facts

- App repo: `C:\Users\VisheshChourasia\OneDrive - Info Origin Technologies Pvt Ltd\Desktop\rag agent`; GitHub `origin` is `https://github.com/Vishesh-afk/RAG-agent.git`; GitLab app mirror remote is `gitlab`.
- At this update, local `main`, `origin/main`, and `gitlab/main` all point to `463548e` (`Add Docker Hub credential diagnostics`). `git status` was clean.
- `.github/workflows/ci.yml` exists. On 2026-11-05, run #5 for commit `715684d` passed validate (syntax, frontend build, SonarQube Quality Gate) and published both DockerHub images. The first direct GitLab `main` commit failed HTTP 403 because the branch is protected. The current local workflow attempts a direct commit to `main` with an idempotence check; verify token bot branch permissions and a successful run before considering promotion complete.
- Images were published to DockerHub repositories `vishesh11/ragagent-backend` (private) and `vishesh11/ragagent-frontend` (public), tagged with commit `463548e5b933d37b27f4ba006be9f7f67dd8921a` at the time of the Argo setup.
- The latest observed SonarQube scan and Quality Gate step succeeded on run #4; a deliberately failing Quality Gate scenario has not been exercised.
- CI-to-GitOps promotion is not yet complete: the direct-to-main workflow change is local and its permission has not been verified. Push it only after reviewing the diff, then confirm a successful GitLab tag commit.
- Keep `.env`, DockerHub tokens, GitHub/GitLab tokens, and Kubernetes Secret values out of source control and chat. GitHub Actions secrets and the in-cluster pull Secret are credential boundaries.
- `frontend/src/lib/api.ts` uses `VITE_API_URL` with a localhost fallback. Verify production routing before setting up a public entry point.
- No public Ingress/ALB has been confirmed. Prior chats intentionally deferred it due to ongoing AWS charges. Explain expected costs before creating one and obtain clear approval.

## GitOps and ArgoCD facts from project chats

- GitOps repo: `https://gitlab.com/visheshchourasia143/rag-agent-gitops.git`, local sibling checkout previously at `C:\Users\VisheshChourasia\OneDrive - Info Origin Technologies Pvt Ltd\Desktop\rag-agent-gitops` (outside this app workspace; verify access/current state before editing).
- Manifests manage API/frontend workloads and Services, probes, and resource settings. PostgreSQL StatefulSet and its existing 8 GiB PVC were intentionally kept outside the app rollout.
- API uses `envFrom` reference `northstar-backend-env`; never replace this with secret values in Git.
- Backend image is private and requires `dockerhub-auth` in namespace `northstar-rag-dev`; chats later confirmed this Secret existed.
- ArgoCD was local on Docker Desktop, with the EKS cluster registered using namespace-scoped service account `argocd-local-reconciler`. Application `northstar-rag-dev` used manual sync. A prior RBAC `ComparisonError` led to setting `resource.respectRBAC: normal`; later chats show Argo could compare/apply the app, but recheck live state.
- Manual sync was chosen as a safety gate while adopting existing resources. Do not switch to auto-sync or enable pruning without checking manifests/diff and confirming the PostgreSQL storage path remains untouched.

## EKS / data / cost guardrails

- Cluster: `northstar-dev-eks`; region: `us-east-2`; namespace: `northstar-rag-dev`.
- The last known PostgreSQL data path was an 8 GiB bound EBS PVC. Preserve it unless the user explicitly chooses otherwise. A later chat discussed using RDS, but no RDS creation or migration is confirmed; verify whether PostgreSQL is currently in EKS or whether the architecture changed.
- User reports the EKS worker node group has been deleted. Keep the node group absent while completing preparation; adding workers and live deployment is the final planned stage. Verify actual AWS state before acting.
- Prior cluster observations mentioned `t3.small` workers and node-group status inconsistencies. A later backend rollout hit disk and capacity limits. Do not assume the old node group is healthy or that a proposed replacement node group was created.
- User is cost-sensitive. EKS control plane, EC2 workers, EBS volumes, load balancers, RDS and monitoring all may incur charges. Check current AWS state/billing and state relevant cost before resource changes.
- Jenkins was a learning baseline that successfully built/pushed ECR images. Jenkins is not part of the selected automated path; do not create or restart Jenkins jobs unless asked.

## Standing workflow

- Before answering “what remains,” inspect this file, current repository status and recent project chats for newer milestones.
- After a meaningful milestone, update the **Current roadmap**, **Immediate resume point**, and any relevant system facts here with date and evidence. Label uncertain/stale states as “last known” and add a concrete recheck step.
- Current sequencing preference: complete CI/GitOps/monitoring/autoscaling/AI-observability preparation first; create EKS workers and deploy the application last.
- Keep explanations short and checkpoint-based. The user prefers practical guidance and AWS Console steps where applicable.
- Never expose secrets or secret values. Do not ask the user to paste them.

| 1 | Application and Docker | Completed baseline. Frontend and backend Dockerfiles and Compose stack exist. |
| 2 | AWS infrastructure | Partially complete. Existing EKS/VPC/node/storage foundation is in use. Avoid rebuilding it. |
| 3 | CI/CD | In progress. Existing Jenkins-to-ECR pipeline is a learning baseline; the revised target is GitHub Actions, SonarQube, DockerHub, and GitOps tag update. |
| 4 | Kubernetes deployment | Next target phase. EKS currently runs the app manually; standardize manifests and let ArgoCD deploy them from Git. |
| 5 | GitOps | Planned: separate GitOps repo, ArgoCD auto-sync and self-heal. |
| 6 | Monitoring and logging | User has a working local Prometheus scrape for the RAG API, Node Exporter, and Prometheus; imported an API dashboard into Grafana and verified request-rate data. New import artifacts: `ops/phase6/grafana/rag-agent-application-cluster-dashboard.json` and `ops/phase6/grafana/northstar-kubernetes-alerts.json`. The latter provisions Grafana-managed rules for pod restarts, high CPU, high memory, and unavailable deployments; replace `PROMETHEUS_DATASOURCE_UID`, mount it under Grafana `provisioning/alerting`, then restart. Dashboard import is via Grafana UI; alert provisioning is separate. Kubernetes panels/rules need kube-state-metrics and kubelet/cAdvisor in Prometheus; current local target evidence does not confirm those metrics. Alert notification contact point/policy separate. Loki/Fluent Bit integration remains unverified. Running container exposed `/metrics`, but checked-out source/dependency files lack instrumentation—resolve before next API image build. |
| 7 | Autoscaling | Planned: HPA first; verify metrics support. Karpenter later, only if needed and after cost review. |
| 8 | AI observability | Planned: Arize Phoenix. |
| 9 | Production readiness | Planned: security, reliability, rollout/rollback, cost, and operational review. |

## Repository baseline (inspected read-only on 2026-11-03)

- Current local repo is the app project. GitHub is remote `origin` (`https://github.com/Vishesh-afk/RAG-agent.git`); GitLab app repo is remote `gitlab` (`https://gitlab.com/visheshchourasia143/rag-agent.git`). The user has now chosen GitHub Actions; treat GitHub as the intended app source of truth after synchronizing it with local `main`. Keep the GitLab copy intact as a backup/reference; do not delete it.
- On 2026-11-03, local `main` was safely merged with GitLab's auto-generated starter README commit, keeping the app's existing README. Merge commit `3481b98` was pushed to GitLab, and local `main` tracks `gitlab/main`. At last inspection GitHub `origin/main` was still at `272a55a`; synchronize it before committing GitHub Actions workflows.
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

## GitLab runner decision

The user saw active GitLab.com instance runners, but reports GitLab will not allow pipeline builds without a credit card/identity verification. GitLab's Free tier can require extra identity verification based on risk. The user chose GitHub Actions instead. Do not configure a `.gitlab-ci.yml` unless the user changes direction. GitHub Free includes hosted-runner usage allowances; public repo standard runner usage is free, while private repo usage is quota/usage-billed. Check repository visibility and Actions usage budgets before enabling potentially billable runs.

## Recommended execution sequence

1. **Protect and inspect current work.** Review the two modified files and `.vscode/` purpose; preserve changes. Confirm `.env` is ignored without reading it.
2. **Use GitHub for application source and Actions.** Synchronize current local `main` to GitHub `origin` after checking visibility; preserve the existing GitLab app copy. Do not push local secrets.
3. **Set up a separate GitHub GitOps repo.** Keep deployment manifests and image tags separate from app code. The already-created GitLab GitOps project can remain untouched as a backup/reference.
4. **Define CI prerequisites.** Decide where SonarQube runs and configure the workflow so a failed Quality Gate blocks release.
5. **Publish images.** Build commit-based/release-versioned frontend and backend images; push to private DockerHub using protected GitHub Actions secrets, never echo credentials.
6. **Prepare Kubernetes desired state.** Create/organize manifests for frontend, backend, and the existing PostgreSQL data path. Add ConfigMaps, Secret handling, probes, resource requests/limits, rolling update settings, Services, and HPA. Validate metrics-server support before HPA. Do not commit plaintext Kubernetes Secret data; choose an appropriate secret delivery pattern before enabling ArgoCD.
7. **Automate GitOps promotion.** After image push and gate success, update the image tag in the separate GitOps repo. Use a narrowly scoped GitHub App or token.
8. **Install/configure ArgoCD.** Watch the GitOps repo and namespace, enable auto-sync/self-heal, and verify that a Git change deploys without manual `kubectl apply`. Define rollback as a Git revert or another explicit, tested release strategy; do not assume ArgoCD automatically rolls back every unhealthy release.
9. **Observe and alert.** Install Prometheus/Grafana in a cost-aware way; add cluster and application dashboards, alerts for pod failures, high CPU/memory, and deployment health. Add Fluent Bit/log collection if required.
10. **Run acceptance exercises.** Deliberately fail Quality Gate, induce Git drift, break a health check, trigger HPA, roll back a bad release, and verify dashboards/alerts. Restore healthy state after each exercise.
11. **Production readiness.** Review IAM/RBAC, image/dependency scanning, secret rotation, backup/restore for PostgreSQL PVC, ingress/TLS/domain costs if public access is wanted, capacity, and operational documentation.

## Immediate next checkpoint

Phase 6 handoff: dashboard JSON is ready at `ops/phase6/grafana/rag-agent-application-cluster-dashboard.json`; import it using **Dashboards → New → Import** and select Prometheus. Alert rules are in `ops/phase6/grafana/northstar-kubernetes-alerts.json`; replace the Prometheus data source UID placeholder and provision the file into `/etc/grafana/provisioning/alerting/` (Grafana dashboard import does not import alert rules). Configure notification contact point/policy separately. Confirm Prometheus scrapes kube-state-metrics and kubelet/cAdvisor before expecting Kubernetes panels and alerts to have data. Preserve existing WSL Compose files and scrape configs. User WSL references: `/home/vishesh/monitoring/prometheus/prometheus.yml`, `/home/vishesh/fluentbit-lab/docker-compose.yml`, `/home/vishesh/fluentbit-lab/loki-config.yaml`.
