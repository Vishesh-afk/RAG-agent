# Grafana app and Kubernetes dashboard + alerts

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
