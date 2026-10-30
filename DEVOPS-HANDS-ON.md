# DevOps hands-on setup

This checkout is the starting application for the AWS EKS learning project. The default Compose stack runs the React frontend, FastAPI API, and PostgreSQL with pgvector.

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

## Learning path

1. Understand and run the application locally.
2. Container and configuration hardening.
3. AWS IAM, VPC, ECR, EKS, and DNS.
4. Bitbucket/Jenkins CI, Snyk scanning, and image publishing.
5. Kubernetes deployment and Argo CD GitOps.
6. Prometheus, Grafana, Fluent Bit, HPA, and Karpenter.
7. LiteLLM and Arize Phoenix integration.
8. Production readiness and failure exercises.
