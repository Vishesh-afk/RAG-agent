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
| 3 | CI and image publishing | Core pipeline is implemented and the latest verified Actions run for `463548e` succeeded: Python syntax check, frontend build, SonarQube scan/Quality Gate, and both DockerHub image pushes. A GitLab GitOps promotion job is now prepared locally in `.github/workflows/ci.yml`; it is not active on GitHub until this change is pushed and `GITLAB_GITOPS_TOKEN` is configured as a repository Actions secret. |
| 4 | Kubernetes deployment | App has been deployed on EKS and accessed using port-forward in prior chats. GitOps manifests were applied through ArgoCD. Latest reported rollout was not healthy: backend image extraction failed with `no space left on device`, and the node reported ephemeral-storage, memory, and pod-capacity pressure. Frontend was healthy; PostgreSQL readiness had timed out, though its 8 GiB PVC remained bound. Recheck live state. |
| 5 | GitOps / ArgoCD | GitLab GitOps repo and dev manifests are in place; `kubectl kustomize` successfully rendered the dev overlay during this turn. ArgoCD is local on Docker Desktop, connected to EKS with namespace-scoped access, and Application `northstar-rag-dev` uses **manual sync**. The CI-to-GitLab image promotion job is prepared locally but awaits push/configuration of `GITLAB_GITOPS_TOKEN`. Argo auto-sync/self-heal is not enabled/verified; keep manual sync as the safety gate. |
| 6 | Monitoring and logging | Not yet confirmed integrated. Prometheus/Grafana and Fluent Bit were discussed/studied, but dashboards and actionable alerts are still to be implemented and verified. |
| 7 | Autoscaling | Not yet confirmed. Configure and test HPA only after EKS metrics support and a healthy baseline are confirmed. Karpenter is optional and deferred pending cost review. |
| 8 | AI observability | Not yet integrated. Arize Phoenix (and LiteLLM in an earlier learning plan) were discussed; confirm scope before implementation. |
| 9 | Production readiness | Remaining: acceptance exercises, access/secrets review, backup/restore, reliability, rollout/rollback, cost review, and operational documentation. |

## Immediate resume point and sequencing

The user reports deleting the EKS worker node group to reduce cost. **Keep workers absent while preparing the remaining components; create a worker node group only as the final step before deploying/testing the application on Kubernetes.** This is the user's chosen order.

1. **Prepare and verify what can be done without worker nodes:** review the GitHub Actions workflow and latest run; decide/implement CI-to-GitOps image-tag promotion; validate the GitOps manifests and secret delivery references; prepare monitoring, autoscaling and AI observability configuration in source control where practical. Avoid applying workloads to EKS while it has no workers.
2. **Recheck AWS billing and cluster state before cloud mutations.** Worker deletion should stop worker EC2 compute charges, but does not stop EKS control-plane charges or charges for retained EBS volumes and other resources. Do not delete the cluster or PostgreSQL volume unless the user explicitly directs it.
3. Before the final deployment stage, resolve the previous worker ephemeral-storage/image-size and capacity issue. The backend image extraction previously failed with `no space left on device`; a large OpenCV layer and retained `uv` cache were identified as possible contributors. Choose appropriate worker instance/disk capacity and communicate costs before creating the node group.
4. **Final infrastructure checkpoint:** recreate the EKS worker node group, verify nodes become Ready, then deploy/sync through ArgoCD and verify PostgreSQL, API and frontend readiness plus Argo Healthy status. Last reported frontend was healthy; backend replacement pod was not ready and PostgreSQL readiness had timed out.
5. Keep Argo manual sync as the safety gate until manifests and deployment are validated. Do not enable auto-sync/pruning without reviewing the diff and confirming database storage is protected.
6. To activate CI-to-GitOps promotion, push the prepared app-repo workflow change and add a GitLab project access token with `api` scope and write permission to the GitOps `main` branch as GitHub Actions secret `GITLAB_GITOPS_TOKEN`. Never put the token in a file or chat. After one successful main-branch run, verify both GitOps image tags match the pushed DockerHub SHA; Argo will show OutOfSync and still wait for manual Sync.

Useful WSL status command (read-only):

```bash
kubectl get nodes
kubectl get pods,services,pvc -n northstar-rag-dev
```

## Repository and CI facts

- App repo: `C:\Users\VisheshChourasia\OneDrive - Info Origin Technologies Pvt Ltd\Desktop\rag agent`; GitHub `origin` is `https://github.com/Vishesh-afk/RAG-agent.git`; GitLab app mirror remote is `gitlab`.
- At this update, local `main`, `origin/main`, and `gitlab/main` all point to `463548e` (`Add Docker Hub credential diagnostics`). `git status` was clean.
- `.github/workflows/ci.yml` exists. The latest observed GitHub Actions run for `463548e` (#4) completed successfully: validate (syntax, frontend build, SonarQube Quality Gate) and publish-images (both image pushes). The local workflow now also includes `promote-gitops`, which uses the GitLab API to update both Kustomize deployment image tags to the triggering commit SHA after successful image publication. This new job needs GitHub secret `GITLAB_GITOPS_TOKEN` and has not yet run.
- Images were published to DockerHub repositories `vishesh11/ragagent-backend` (private) and `vishesh11/ragagent-frontend` (public), tagged with commit `463548e5b933d37b27f4ba006be9f7f67dd8921a` at the time of the Argo setup.
- The latest observed SonarQube scan and Quality Gate step succeeded on run #4; a deliberately failing Quality Gate scenario has not been exercised.
- The GitOps promotion workflow is prepared locally but not yet active on GitHub; no completed CI-driven GitLab commit is evidenced. Until its commit is pushed and the token secret is present, image-tag promotion remains manual.
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

