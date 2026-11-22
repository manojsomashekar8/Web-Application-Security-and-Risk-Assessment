"""Apply migrations, then set the read-only Grafana role password from GRAFANA_DB_PASSWORD."""
import os

from psycopg import sql

from src import db

if __name__ == "__main__":
    with db.connect() as conn:
        print("applied:", db.migrate(conn) or "none (up to date)")
        # A scan's worker thread dies with the backend, so any scan still 'running' at startup was interrupted.
        stale = conn.execute("UPDATE scans SET status='failed', finished_at=now(), error=%s "
                             "WHERE status='running' RETURNING id",
                             ("interrupted: the backend stopped during this scan",)).fetchall()
        print("marked interrupted scans failed:", [r["id"] for r in stale] or "none")
        conn.execute(sql.SQL("ALTER ROLE grafana_ro PASSWORD {}").format(sql.Literal(os.environ["GRAFANA_DB_PASSWORD"])))
