# -*- coding: utf-8 -*-
"""Compare tables existing in MySQL hr_recruitment_db vs. SQLAlchemy metadata."""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

import pymysql

from app import create_app
from app.extensions import db

HOST = "rm-8vb7m858r8wt3b10hjo.mysql.zhangbei.rds.aliyuncs.com"


def main() -> None:
    pwd = (BACKEND / "scripts" / ".pwd_secret").read_text(encoding="utf-8").strip()
    conn = pymysql.connect(host=HOST, port=3306, user="hr_recruitment",
                           password=pwd, database="hr_recruitment_db",
                           charset="utf8mb4")
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION()")
        print("MySQL version:", cur.fetchone()[0])
        cur.execute("SHOW TABLES")
        existing = sorted(r[0] for r in cur.fetchall())
    conn.close()
    print("CONNECTED OK")

    import app.models  # noqa: F401  ensure all models registered on db.metadata
    flask_app = create_app()
    with flask_app.app_context():
        model_tables = sorted(db.metadata.tables.keys())

    existing_set, model_set = set(existing), set(model_tables)
    print("\n== MySQL existing tables (%d):" % len(existing))
    for t in existing:
        print("  ", t)
    print("\n== Model tables (%d):" % len(model_tables))
    for t in model_tables:
        print("  ", t)
    print("\n== In model but MISSING in MySQL:", sorted(model_set - existing_set))
    print("== In MySQL but EXTRA (not in model):", sorted(existing_set - model_set))
    print("== Consistent:", sorted(existing_set & model_set))


if __name__ == "__main__":
    main()
