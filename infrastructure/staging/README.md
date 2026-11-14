# Staging environment plan

Use a separate tenant, DNS name, identity realm, PostgreSQL database and artifact store. Populate synthetic or deliberately selected public-source fixtures. Before promotion, run the named GitHub Actions checks, perform the Keycloak smoke, compare generated PDF digests and rehearse restoring a snapshot. Treat staging credentials and service endpoints as separate configuration.
