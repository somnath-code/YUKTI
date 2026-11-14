import re
from typing import Any
import jwt
from packages.core.settings import Settings, policy
from packages.identity.access import Principal


class TokenVerifier:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.keys = jwt.PyJWKClient(settings.jwks_url, timeout=4)

    def verify(self, token: str) -> Principal:
        if len(token) > 12_000 or jwt.get_unverified_header(token).get('alg') != 'RS256':
            raise jwt.InvalidTokenError('Unexpected token format')
        key = self.keys.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=['RS256'], audience=self.settings.audience,
                            issuer=self.settings.issuer,
                            options={'require': ['exp', 'iat', 'aud', 'iss', 'sub', policy('access')['tenant_claim']]})
        return self.principal(claims)

    @staticmethod
    def principal(claims: dict[str, Any]) -> Principal:
        tenant = claims[policy('access')['tenant_claim']]
        if not isinstance(tenant, str) or not re.fullmatch('[a-z][a-z0-9-]{1,49}', tenant):
            raise jwt.InvalidTokenError('Invalid tenant')
        roles = claims.get('realm_access', {}).get('roles', [])
        if not isinstance(roles, list) or any(not isinstance(role, str) for role in roles):
            raise jwt.InvalidTokenError('Invalid roles')
        return Principal(claims['sub'], tenant, frozenset(roles))
