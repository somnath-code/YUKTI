from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
import json


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def encoded(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def audit(tx, tenant: str, actor: str, action: str, entity: str, details: dict) -> None:
    tx.run(
        'INSERT INTO audit_log(tenant,id,actor,action,entity,details,occurred_at) VALUES (%s,%s,%s,%s,%s,%s,%s)',
        (tenant, uuid4().hex, actor, action, entity, encoded(details), now()),
    )
