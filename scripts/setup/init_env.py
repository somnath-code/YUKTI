from pathlib import Path
from secrets import token_urlsafe
import os

path = Path('.env')
if path.exists():
    raise SystemExit('.env already exists. Keep it or move it before generating new values.')
descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(descriptor, 'w') as stream:
    for key in ('POSTGRES_PASSWORD', 'DB_APP_PASSWORD', 'KC_ADMIN_PASSWORD'):
        stream.write(f'{key}={token_urlsafe(30)}\n')
    stream.write('SCHEDULER_TENANT=demo\nLIVE_FEEDS=0\nOLLAMA_MODEL=qwen2.5:1.5b\n')
print('Created .env with independently generated local secrets')
