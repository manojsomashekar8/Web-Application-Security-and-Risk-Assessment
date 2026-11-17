"""Apply migrations, then set the read-only Grafana role password from GRAFANA_DB_PASSWORD."""
import os

from psycopg import sql

from src import db

if __name__ == "__main__":
    with db.connect() as conn:
        print("applied:", db.migrate(conn) or "none (up to date)")
        conn.execute(sql.SQL("ALTER ROLE grafana_ro PASSWORD {}").format(sql.Literal(os.environ["GRAFANA_DB_PASSWORD"])))
