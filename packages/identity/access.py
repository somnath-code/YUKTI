from dataclasses import dataclass
from packages.core.settings import policy

@dataclass(frozen=True)
class Principal:
    subject: str
    tenant: str
    roles: frozenset[str]

    def can(self, permission: str) -> bool:
        return permission in policy('permissions')['permissions'] and any(
            permission in policy('iam').get(role, ()) for role in self.roles)
