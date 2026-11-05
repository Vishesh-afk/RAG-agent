# AI Project Guide

This file is a current, code-based guide for AI assistants and developers working in this repository. It describes what is present in the checkout, how the main pieces work, and what still needs implementation. Update it when the code or project direction changes.

## Project summary

This repository contains a document-question-answering RAG application. Users upload PDF files, the backend extracts and chunks their content, creates embeddings, and stores documents and chunks in PostgreSQL with pgvector. A Pydantic AI agent can search those chunks and answer questions. Chat history is stored by session.

The main user interface is a React + TypeScript web app. A Streamlit interface remains available as an optional, older/alternate UI. The project also contains Docker Compose configuration and CI workflows.

## What is implemented

- FastAPI backend in `agent/api.py` for chat, streaming chat, health, document ingestion and management, search, and session history.
- Pydantic AI agent in `agent/agent.py` with vector search, hybrid search, document lookup, and document listing tools.
- PostgreSQL access and persistence in `agent/db_utils.py`; the schema is initialized from `sql/schema.sql` and uses pgvector, UUIDs, trigram search, and PostgreSQL full-text search.
- PDF ingestion in `ingestion/`: Docling extraction with a pypdf fallback, semantic or recursive chunking, OpenAI embeddings, and transactional document/chunk writes.
- React chat interface in `frontend/` with streamed responses, session ID retention in browser session storage, health polling, document listing, uploads, and deletion controls.
- Alternate Streamlit interface in `ui/app.py`, served through the backend API.
- Docker Compose services for PostgreSQL, API, and React frontend. Streamlit is opt-in with the `streamlit` profile.
- GitHub Actions workflow at `.github/workflows/ci.yml`: Python syntax compilation, frontend production build, SonarQube Cloud scan with Quality Gate waiting, and Docker Hub publishing on pushes to `main` after validation succeeds.
- A GitLab CI workflow at `.gitlab-ci.yml` that checks Python syntax and builds the frontend.
- Unit-focused tests for models, database helpers, and chunking under `tests/`.

## Repository map

| Path | Purpose |
|---|---|
| `agent/` | FastAPI API, Pydantic AI agent, tools, provider configuration, models, and database helpers |
| `ingestion/` | PDF extraction, chunking, embeddings, and database ingestion pipeline |
| `frontend/` | React + TypeScript + Vite user interface and Nginx container config |
| `ui/` | Optional Streamlit user interface |
| `sql/schema.sql` | Tables, indexes, database functions, triggers, and view |
| `tests/` | Pytest fixtures and tests for models, DB helpers, and chunking |
| `documents/` | Local PDF examples/input data; excluded from Docker build contexts and ignored by Git |
| `.github/workflows/ci.yml` | GitHub validation, SonarQube, and image publishing workflow |
| `.gitlab-ci.yml` | GitLab syntax/build validation workflow |
| `docker-compose.yml` | Local multi-service app stack |
| `docker-compose.override.yml` | Local development mounts and API reload settings |
| `ops/phase6/grafana/` | Grafana dashboard JSON for RAG API + Kubernetes metrics, and Grafana alert-rule provisioning JSON |
| `ops/phase6/local/` | Prometheus scrape fragment and local API alert reference/runbook |
| `PROJECT_MEMORY.md` | Older project continuity and cloud-roadmap notes; parts may be stale compared with this guide and current files |
| `DEVOPS-HANDS-ON.md` | Local setup and older learning roadmap; roadmap mentions Bitbucket/Jenkins and may not match the newer GitHub Actions direction |

The `ops/phase6/grafana/` directory contains a dashboard import JSON and a separate Grafana alert provisioning JSON. The dashboard covers API, Node Exporter, and Kubernetes workload queries for namespace `northstar-rag-dev`. The alert file defines pod restart, high CPU, high memory, and unavailable deployment rules. The alert file is provisioned into Grafana's `/etc/grafana/provisioning/alerting` directory; it is not imported through the dashboard importer. Replace its `PROMETHEUS_DATASOURCE_UID` placeholder with the actual Grafana Prometheus data-source UID before provisioning. The local Prometheus shown by the user has API, Node Exporter, and Prometheus targets but no verified Kubernetes scrape target; Kubernetes dashboard panels and alerts require kube-state-metrics and kubelet/cAdvisor metrics. Do not claim cluster monitoring is live until those targets are configured and verified.

The API source now registers `prometheus-fastapi-instrumentator` and exposes `/metrics` (excluding `/health` and `/metrics` from request counts); the dependency is declared in both `pyproject.toml` and `requirements.txt`. After source changes, rebuild the API container so Prometheus receives this route. A Prometheus target error of HTTP 404 means the currently running image lacks the route or the scrape path is wrong; check `http://localhost:8058/metrics` first.

## Main request and data flows

### Ingest a PDF

1. The frontend sends a PDF to `POST /ingest` with `clean`, `include_tables`, and `include_images` options.
2. The API reuses a cached ingestion pipeline for the selected extraction options.
3. Docling extracts PDF content and metadata. If extraction fails, the pipeline falls back to pypdf text extraction.
4. The chunker uses semantic splitting when enabled and applicable; recursive character splitting is the fallback.
5. OpenAI embeddings are generated and the document plus chunks are saved to PostgreSQL.
6. The frontend refreshes its document list.

The command-line entry point is `python -m ingestion.ingest`. It supports a folder or one PDF, cleaning existing records, chunk settings, and disabling semantic splitting, image extraction, or table extraction. Review the `--clean` behavior before using it: it deletes existing messages, sessions, chunks, and documents.

### Ask a question

1. The frontend posts to `POST /chat/stream` and reads server-sent events.
2. The API finds or creates a session and adds recent conversation context to the prompt.
3. The Pydantic AI agent chooses among its registered search/document tools.
4. Search generates an embedding and uses either vector search or the SQL hybrid search function. Hybrid search combines vector similarity and PostgreSQL full-text ranking.
5. Text and tool events stream to the frontend; the completed user/assistant turn is persisted.

The frontend currently sends `user_id: "web-user"` and requests hybrid search. Session continuity is stored in `sessionStorage`; this is browser-session persistence, not a user authentication system.

## Backend API routes

- `GET /health`
- `POST /chat`
- `POST /chat/stream`
- `POST /ingest`
- `POST /search/vector`
- `POST /search/hybrid`
- `GET /documents`
- `DELETE /documents`
- `DELETE /documents/{document_id}`
- `GET /sessions/{session_id}`
- FastAPI docs are available at `/docs` when the API is running.

For exact request and response models, use `agent/models.py` and the route implementations in `agent/api.py`; update this list if routes change.

## Local development

### Docker Compose

1. Create a local `.env` from `.env.example` and provide a valid OpenAI API key when using embeddings or chat. Keep `.env` private; never read its values into logs or commit it.
2. Start the default stack:

   ```sh
   docker compose up --build
   ```

3. Open the frontend at `http://localhost:3000`, API docs at `http://localhost:8058/docs`, and PostgreSQL at host port `6543` if needed.
4. To include Streamlit, run `docker compose --profile streamlit up --build`; the UI uses the configured server port, normally `8501`.

The Compose stack persists PostgreSQL data in `postgres_data` and uploaded documents in `documents_data`. `docker compose down -v` removes those local volumes and their data.

### Run services directly

Install Python dependencies from `pyproject.toml` in Python 3.12, install frontend dependencies with `npm ci` in `frontend/`, and ensure PostgreSQL/pgvector and environment settings are available. Start the backend with:

```sh
uvicorn agent.api:app --host 0.0.0.0 --port 8058 --reload
```

Start the frontend separately with `npm run dev` from `frontend/`. The Vite app uses `VITE_API_URL` when set and otherwise defaults to `http://localhost:8058`.

## Configuration and external services

Configuration is loaded from environment variables and `.env`. `.env.example` lists the intended local variables: API host/port and logging, database host/port/name/user/password, OpenAI API key, LLM choice, embedding model, and optional Streamlit host/port. Do not copy secrets into this file or this guide.

The agent uses the OpenAI-compatible Pydantic AI provider. Embeddings use `text-embedding-3-small` by default; the SQL functions and vector column are currently sized for 1536 dimensions. If changing embedding models, check vector dimensions and re-ingest existing content as needed.

Some defaults differ by launch path: for example, `agent/api.py` has an `APP_PORT` fallback of `8000`, while the Compose configuration and `.env.example` use `8058`. Prefer explicit environment settings and check the actual launch configuration before debugging a port mismatch.

## Database outline

`sql/schema.sql` creates:

- `documents`: document title, source, full content, metadata, timestamps.
- `chunks`: document-linked chunk text, 1536-dimensional embedding, order, metadata, and token count.
- `sessions` and `messages`: user/session metadata and persisted conversation history.
- HNSW vector, document/chunk, trigram, full-text, metadata, timestamp, and session indexes.
- `match_chunks`, `hybrid_search`, and `get_document_chunks` functions plus timestamp triggers and a `document_summaries` view.

The API initializes the schema at startup. The schema file is the source of truth for SQL behavior; keep database helpers and schema changes aligned.

## Tests and checks

Tests currently cover Pydantic models, database helper behavior, and chunker behavior. Run the suite with:

```sh
pytest
```

The GitHub Actions workflow currently runs `python -m compileall -q agent ingestion ui` and the frontend production build before the SonarQube scan. It does not currently run pytest. The Docker publishing job runs only on pushes to `main` and publishes backend and frontend images tagged with the commit SHA and `latest` after validation succeeds. SonarQube organization/project variables, `SONAR_TOKEN`, and Docker Hub credentials must be configured in GitHub for those jobs to succeed. Do not expose credential values in logs.

No tests or builds were run while preparing this guide.

## Current monitoring handoff (2026-11-05)

- The user verified local RAG API metrics in Prometheus and imported an API dashboard into Grafana; the API request-rate query returned data.
- `ops/phase6/grafana/rag-agent-application-cluster-dashboard.json` is the combined app/cluster dashboard import. `ops/phase6/grafana/northstar-kubernetes-alerts.json` contains Grafana-managed workload alerts for restarts, CPU, memory, and unavailable deployments. Alert rules use file provisioning, not Dashboard → Import; replace `PROMETHEUS_DATASOURCE_UID`, mount the file under `/etc/grafana/provisioning/alerting/`, and restart Grafana.
- The local Prometheus screenshot confirmed RAG API, Node Exporter, and Prometheus targets. Kubernetes workload panels and alerts still need kube-state-metrics and kubelet/cAdvisor metrics from EKS namespace `northstar-rag-dev`; they are not confirmed live.
- The running API container exposed `/metrics`, but the checked-out `agent/api.py` and dependency files do not include metrics instrumentation. Reconcile before rebuilding/publishing an API image.
- User-provided WSL references: `/home/vishesh/monitoring/prometheus/prometheus.yml`, `/home/vishesh/fluentbit-lab/docker-compose.yml`, `/home/vishesh/fluentbit-lab/loki-config.yaml`. Preserve their existing WSL config and scrape jobs; the Loki/Fluent Bit lab is not yet integrated.
- The API source now registers `prometheus-fastapi-instrumentator` and exposes `/metrics`; the dependency is declared in `pyproject.toml` and `requirements.txt`. A current scrape returned HTTP 404, so rebuild the API image and check `http://localhost:8058/metrics` before evaluating Prometheus again.
- A WSL Compose rebuild initially failed because `docker-compose.override.yml` still declared an obsolete `ui` service after it was removed from the base compose. The orphan override was removed; `docker compose config --services` now succeeds and lists `postgres`, `api`, and `web`. Retry from the RAG app project directory.

## DevOps / deployment status from this checkout

**Present:** local Docker Compose; backend and frontend Dockerfiles; GitHub CI validation, SonarQube Quality Gate scan, and Docker Hub image publishing; GitLab syntax/frontend-build validation workflow.

**Not present in the app repository:** Kubernetes deployment manifests/charts, the separate GitOps configuration, ArgoCD configuration, HPA configuration, or a CI step that updates a GitOps repository. Grafana dashboard/alert artifacts exist under `ops/phase6/grafana/`; live cluster metric collection is not configured here. External AWS/EKS resources or past manual deployments cannot be confirmed from these files; verify live state separately before relying on it.

The GitHub workflow only builds and publishes images. Image publication does not itself deploy them to Kubernetes.

## Working guidance for future AI assistants

- Read this guide and inspect the relevant source before changing behavior. Treat code as authoritative if this guide is stale, then update the guide to match.
- Preserve user changes and inspect `git status` before editing, staging, or committing.
- Never read, print, commit, or expose `.env`, API keys, Docker credentials, or Kubernetes Secret values.
- Keep local sample PDFs and personal documents private; ingest only files the user intends to use.
- Preserve existing PostgreSQL data unless the user explicitly requests a destructive reset. Confirm effects before using `--clean` or deleting volumes.
- Do not claim cloud deployment, automated GitOps, monitoring, or autoscaling is complete without current evidence.
- The repo has both GitHub (`origin`) and GitLab (`gitlab`) remotes in the inspected checkout. The checked-out `main` branch was tracking `gitlab/main` at inspection. Confirm branch, remotes, and sync state before pushing; do not remove either remote or push without explicit task context.
- The older `PROJECT_MEMORY.md` contains roadmap and AWS/EKS notes that are not verifiable from the application source. Treat those as historical user-provided context, not current infrastructure proof. The app source of truth is GitHub per the latest stated direction, but the local branch tracking information should be checked before synchronization.

## Current inspection note

This guide was prepared on 2026-11-05 from the repository files and tracked layout. At inspection, `git status` was clean on `main`, tracking `gitlab/main`; both `origin` (GitHub) and `gitlab` remotes were configured. Recheck these mutable facts when resuming work.
