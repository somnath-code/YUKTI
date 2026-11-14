# Grafana dashboard

Add a Prometheus data source with UID yukti-prometheus. Import yukti-local.json and select a Prometheus instance that can reach the API. The dashboard uses the upstream scrape status and labels. Grafana can be run separately. The Compose monitoring profile starts Prometheus and evaluates the bundled alert rules. It does not send alerts to external recipients.
