# Account and tenant administration

The realm seeds roles and the public PKCE client. Create each account with a tenant_id value such as demo in the Keycloak management console. The tenant_id field is declared as admin-only in the realm user profile. Grant only the realm roles needed for that account. Keep separate editor, approver and publisher accounts for a full issue walkthrough.

Use the authority returned by the realm's discovery endpoint as OIDC_ISSUER. The backend may use a separate internal OIDC_JWKS_URL for key verification. Keycloak access tokens must include the yukti-api audience and the tenant_id claim. Keep the console redirect URI and web origin explicit. Browser apps use localhost for development and need HTTPS on a real host.

Rotate credentials from the identity service and revoke user sessions when memberships change. Archive release changes the state of an edition within the publisher's own tenant. The private Sites deployment uses its independent owner-only privacy setting.
