# API reference

FastAPI serves OpenAPI at `/docs`. Send `Authorization: Bearer <Keycloak access token>` to protected routes. Read their request schemas in OpenAPI.

| Route | Method | Required permission or behavior |
| --- | --- | --- |
| /health | GET | Database reachability |
| /api/session | GET | Verified user claims |
| /api/evidence | GET | Draft read |
| /api/evidence/{urn}/suggest | POST | Article edit, model available |
| /api/articles | POST | Article ingest |
| /api/articles/{id}?revision=N | PUT | Article edit, matching revision |
| /api/articles | GET | Draft read |
| /api/quality | POST | Draft read, preflight supplied brief |
| /api/articles/{id}/language | POST | Draft read |
| /api/articles/{id}/review | POST | Article review |
| /api/search | GET | Draft read, optional q, topic and kind |
| /api/search/hybrid?q=… | GET | Draft read, merged keyword and vector ranking |
| /api/semantic?q=… | GET | Draft read, embedding model available |
| /api/issues | POST | Issue create |
| /api/issues | GET | Archive read. Draft metadata requires draft read |
| /api/issues/{id}/pdf | GET | Archive read. Draft PDF requires draft read |
| /api/issues/{id}/approve | POST | Issue approve, matching checksum |
| /api/issues/{id}/release | POST | Issue release, approved checksum |
| /api/platform | GET | Audit read, tenant counts and policy summary |
| /api/audit | GET | Audit read |

401 means missing or invalid credentials. 403 means the role or separation of duties denied the action. 404 covers absent or concealed records. 409 covers conflicts, stale revisions or invalid issue transitions. 422 covers rejected inputs, checks, or layouts. Model, artifact and grammar failures can yield 503. The grammar precheck explicitly reports its availability.
