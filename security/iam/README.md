# Identity boundaries

Keycloak issues RS256 tokens for the intended issuer and audience. The API derives role and tenant authority from verified claims. Only a realm administrator can assign tenant_id. Separate editorial, approval, release and audit roles. See config/iam and docs/iam for role mapping and account provisioning.
