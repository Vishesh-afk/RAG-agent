# Grafana app and Kubernetes dashboard + alerts

## Local Docker monitoring setup

The local Prometheus container is already configured to scrape `rag-agent-api` at
`host.docker.internal:8058/metrics`, along with Prometheus and Node Exporter. The
RAG API target was verified `UP` at `http://localhost:9090/targets`.

To provision the Prometheus data source and dashboard into the running Grafana
container from the repository root:

```powershell
docker cp .\ops\phase6\grafana\provisioning\datasources\prometheus.yml grafana:/etc/grafana/provisioning/datasources/prometheus.yml
docker cp .\ops\phase6\grafana\provisioning\dashboards\rag-agent.yml grafana:/etc/grafana/provisioning/dashboards/rag-agent.yml
docker exec grafana mkdir -p /var/lib/grafana/dashboards/rag-agent
docker cp .\ops\phase6\grafana\provisioning\dashboards\rag-agent.json grafana:/var/lib/grafana/dashboards/rag-agent/rag-agent.json
docker restart grafana
```

Grafana is available at `http://localhost:3001`. The dashboard will be under
the **RAG Agent** folder. The provisioning files are kept in this repository;
repeat the copy steps if the Grafana container is recreated. API and Node
Exporter panels work with the local targets. Kubernetes panels require
Kubernetes metrics sources and will remain empty until those are scraped.

## Dashboard

Import `rag-agent-application-cluster-dashboard.json` from **Dashboards → New → Import** and choose the Prometheus data source. It includes API availability, request volume/rate, server errors, p95 latency, pod readiness/restarts, pod CPU/memory, and node CPU/memory.

## Grafana-managed workload alert rules

`northstar-kubernetes-alerts.json` is Grafana alerting file-provisioning JSON, not a dashboard JSON. Grafana's dashboard import page cannot import alert rules. To load these rules into Grafana OSS:

1. In Grafana, open **Connections → Data sources → Prometheus** and copy its UID from the data-source details page.
2. Replace every `PROMETHEUS_DATASOURCE_UID` in the alert JSON with that UID.
3. Copy the JSON into the monitoring Compose project's mounted Grafana provisioning directory at `alerting/northstar-kubernetes-alerts.json`; the directory must be mounted in the container at `/etc/grafana/provisioning/alerting`.
4. Restart Grafana from its monitoring Compose directory. The four rules will appear under **Alerting → Alert rules**.

File-provisioned alert rules are managed by their file and are read-only in the Grafana UI. To edit them, change the JSON and reload/restart Grafana. A contact point and notification policy are separate; add them if you want messages delivered.

## Metrics prerequisites

The local Prometheus setup currently has the RAG API, Prometheus, and Node Exporter targets. It does not currently scrape Kubernetes. The app and node panels should work with the local setup. Pod, deployment, CPU-request, and memory-request panels and alert rules need Kubernetes metrics from kube-state-metrics and kubelet/cAdvisor for the `northstar-rag-dev` namespace. Until those sources are scraped, cluster panels may show no data and cluster rules stay Normal due to `noDataState: OK`.
