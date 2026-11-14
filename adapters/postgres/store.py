from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Any

from packages.core.settings import ROOT


class Tx:
    def __init__(self, conn: Any, pg: bool):
        self.conn, self.pg = conn, pg

    def run(self, sql: str, args: Sequence[Any] = ()):
        return self.conn.execute(sql if self.pg else sql.replace('%s', '?'), args)

    def one(self, sql: str, args: Sequence[Any] = ()) -> dict | None:
        row = self.run(sql, args).fetchone()
        return dict(row) if row else None

    def all(self, sql: str, args: Sequence[Any] = ()) -> list[dict]:
        return [dict(row) for row in self.run(sql, args)]


class Database:
    def __init__(self, url: str):
        self.url = url
        self.pg = url.startswith(('postgresql://', 'postgres://'))
        if not self.pg and not url.startswith('sqlite:///'):
            raise ValueError('Use a PostgreSQL URL or a local SQLite file')

    def connect(self):
        if self.pg:
            import psycopg
            from psycopg.rows import dict_row
            return psycopg.connect(self.url, row_factory=dict_row, connect_timeout=5)
        filename = self.url.removeprefix('sqlite:///')
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(filename, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        return conn

    @contextmanager
    def transaction(self, tenant: str, *, write: bool = False) -> Iterator[Tx]:
        conn = self.connect()
        try:
            tx = Tx(conn, self.pg)
            if self.pg:
                tx.run("SELECT set_config('app.tenant_id', %s, true)", (tenant,))
            elif write:
                tx.run('BEGIN IMMEDIATE')
            yield tx
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def migrate(self) -> None:
        conn = self.connect()
        try:
            conn.execute('CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)')
            if self.pg:
                conn.execute('SELECT pg_advisory_xact_lock(462883)')
            for path in sorted((ROOT / 'database' / 'migrations').glob('*.sql')):
                if path.name.endswith('.postgresql.sql') and not self.pg:
                    continue
                tx = Tx(conn, self.pg)
                if tx.one('SELECT name FROM schema_migrations WHERE name=%s', (path.name,)):
                    continue
                if self.pg:
                    conn.execute(path.read_text())
                else:
                    # SQLite executes each statement inside the caller's transaction.
                    if not conn.in_transaction:
                        conn.execute('BEGIN IMMEDIATE')
                    for statement in path.read_text().split(';'):
                        if statement.strip():
                            conn.execute(statement)
                tx.run('INSERT INTO schema_migrations VALUES (%s)', (path.name,))
            conn.commit()
        finally:
            conn.close()
