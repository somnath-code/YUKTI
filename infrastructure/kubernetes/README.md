# Kubernetes rollout plan

Use a private namespace with restricted egress and Kubernetes NetworkPolicy. Deploy multiple stateless API replicas behind an authenticated ingress. Readiness probes should exercise database reachability and liveness probes should avoid dependent outages. Mount credentials from the approved secret store. Keep rendering and bulk work on capped worker queues. Choose persistence and identity services before authoring environment-specific manifests.

The base includes a private ClusterIP and one restricted API replica. Supply a locally built or private registry image through your Kustomize overlay, a retained yukti-artifacts claim, and a yukti-runtime-env secret containing DATABASE_URL, OIDC_ISSUER, OIDC_JWKS_URL and LANGUAGETOOL_URL. The runtime database and identity dependencies live outside the base. Use a suitable storage policy before increasing replicas. No public ingress is included.
