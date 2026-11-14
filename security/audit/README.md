# Audit

Successful article and issue mutations write actor, tenant, action, identifier, details and a UTC timestamp in the same transaction. Auditors see their own tenant events. This local database audit is append-by-application behavior. Use an independently controlled retention and integrity mechanism for production.
