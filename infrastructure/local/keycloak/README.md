# Local Keycloak

The local realm import declares the editor, curator, approver, publisher, auditor and reader roles, an admin-only tenant attribute and a PKCE client. It seeds no accounts or secrets. The bootstrap password is generated in .env. Manage users with scripts.setup.create_local_users or the loopback Keycloak administration console.
