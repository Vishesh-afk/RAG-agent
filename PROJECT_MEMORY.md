# RAG Agent DevOps Project Memory

Last updated: 2026-11-05

Use this file as the project continuity note before making recommendations or changes. It reflects the local repository and the recent Codex project chats. Prefer the newest verified state over older roadmap notes. Teach one practical checkpoint at a time in plain language, explain AWS cost implications before cost-incurring changes, and never read, print, commit, or expose `.env` or other secret values.

## Target outcome

Build and demonstrate an end-to-end DevOps flow for the RAG Agent (React frontend, FastAPI backend, PostgreSQL/pgvector): GitHub Actions CI, SonarQube Quality Gate, DockerHub image publishing, GitOps manifests in a separate GitLab repo, ArgoCD deployment to EKS, then monitoring, autoscaling, AI observability, and production-readiness exercises.

The user has emphasized that work they believe is complete should be checked against prior project chats before being marked remaining. Keep this file current after meaningful milestones and use it to resume work.

## Current roadmap

| Phase | Area | Status / last known evidence |
|---|---|---|
| 1 | Application and Docker | Baseline complete: React frontend, FastAPI backend, PostgreSQL/pgvector, Dockerfiles and Compose stack. |
| 2 | AWS infrastructure | Partly complete. Existing EKS/VPC was used. **User reports the EKS worker node group has now been deleted** to reduce costs. The cluster control plane and retained EBS/storage or other AWS resources may still incur charges. Do not recreate workers until the final deployment checkpoint. |
| 3 | CI and image publishing | Core pipeline is implemented. New run `715684d` passed syntax, frontend build and SonarQube Quality Gate, then successfully pushed both images. Its first GitLab promotion attempt was rejected (HTTP 403) because it tried to write directly to protected `main`. Workflow now prepares a feature branch and merge request instead; this fix is local and needs a push plus a confirming run. |
| 4 | Kubernetes deployment | App has been deployed on EKS and accessed using port-forward in prior chats. GitOps manifests were applied through ArgoCD. Latest reported rollout was not healthy: backend image extraction failed with `no space left on device`, and the node reported ephemeral-storage, memory, and pod-capacity pressure. Frontend was healthy; PostgreSQL readiness had timed out, though its 8 GiB PVC remained bound. Recheck live state. |
| 5 | GitOps / ArgoCD | GitLab GitOps repo and dev manifests are in place; `kubectl kustomize` successfully rendered the dev overlay during this turn. ArgoCD is local on Docker Desktop, connected to EKS with namespace-scoped access, and Application `northstar-rag-dev` uses **manual sync**. GitHub Actions has the GitLab token; the initial direct-to-main promotion was blocked by HTTP 403. The workflow is being changed to open a merge request from a feature branch; after merge, Argo still requires a manual Sync. Auto-sync/self-heal is not enabled/verified. |
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
6. Push the revised app-repo workflow; the GitLab access token is already configured as `GITLAB_GITOPS_TOKEN`. Verify a passing release opens a GitLab merge request with both GitOps image tags set to the new SHA. Merge the MR, then review Argo's diff and manually Sync after workers are recreated and the cluster is healthy.

Useful WSL status command (read-only):

```bash
kubectl get nodes
kubectl get pods,services,pvc -n northstar-rag-dev
```

## Repository and CI facts

- App repo: `C:\Users\VisheshChourasia\OneDrive - Info Origin Technologies Pvt Ltd\Desktop\rag agent`; GitHub `origin` is `https://github.com/Vishesh-afk/RAG-agent.git`; GitLab app mirror remote is `gitlab`.
- At this update, local `main`, `origin/main`, and `gitlab/main` all point to `463548e` (`Add Docker Hub credential diagnostics`). `git status` was clean.
- `.github/workflows/ci.yml` exists. On 2026-11-05, run #5 for commit `715684d` passed validate (syntax, frontend build, SonarQube Quality Gate) and published both DockerHub images. The first `promote-gitops` implementation attempted to commit directly to protected GitLab `main` and failed HTTP 403. Updated local workflow uses a feature branch and GitLab merge request, with an idempotence check; the token is already configured. The revised workflow must be pushed and run before promotion is considered complete.
- Images were published to DockerHub repositories `vishesh11/ragagent-backend` (private) and `vishesh11/ragagent-frontend` (public), tagged with commit `463548e5b933d37b27f4ba006be9f7f67dd8921a` at the time of the Argo setup.
- The latest observed SonarQube scan and Quality Gate step succeeded on run #4; a deliberately failing Quality Gate scenario has not been exercised.
- CI-to-GitOps promotion is not yet complete: no GitLab merge request has been created. The revised branch-and-MR workflow is local; push it and confirm the job creates an MR before marking this done.
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

