"""PostgreSQL access. Connection string comes from DATABASE_URL (set by docker-compose)."""
import os
import pathlib

import psycopg
from psycopg.rows import dict_row

MIGRATIONS = pathlib.Path(__file__).resolve().parents[1] / "db" / "migrations"


def connect() -> psycopg.Connection:
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row, autocommit=True)


def migrate(conn: psycopg.Connection) -> list[str]:
    applied = []
    done = {r["version"] for r in conn.execute("SELECT version FROM schema_migrations").fetchall()} \
        if _table_exists(conn, "schema_migrations") else set()
    for path in sorted(MIGRATIONS.glob("*.sql")):
        if path.stem in done:
            continue
        conn.execute(path.read_text())
        conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
        applied.append(path.stem)
    return applied


def _table_exists(conn, name: str) -> bool:
    return conn.execute("SELECT to_regclass(%s) IS NOT NULL AS ok", (name,)).fetchone()["ok"]
