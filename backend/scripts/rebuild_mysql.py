# -*- coding: utf-8 -*-
"""Drop ALL tables in MySQL hr_recruitment_db, then recreate from SQLAlchemy metadata."""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

_pwd = (BACKEND / "scripts" / ".pwd_secret").read_text(encoding="utf-8").strip()
os.environ["DATABASE_URL"] = (
    "mysql+pymysql://hr_recruitment:%s@"
    "rm-8vb7m858r8wt3b10hjo.mysql.zhangbei.rds.aliyuncs.com:3306"
    "/hr_recruitment_db?charset=utf8mb4" % _pwd
)

from sqlalchemy import text

from app import create_app
from app.extensions import db


def main() -> None:
    import app.models  # noqa: F401
    flask_app = create_app()
    with flask_app.app_context():
        engine = db.engine
        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
            rows = conn.execute(text("SHOW TABLES")).fetchall()
            for (tname,) in rows:
                conn.execute(text("DROP TABLE IF EXISTS `%s`" % tname))
                print("dropped:", tname)
            conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
            conn.commit()
        db.create_all()
        remaining = sorted(db.metadata.tables.keys())
        print("\ncreated %d tables:" % len(remaining))
        for t in remaining:
            print("  ", t)


if __name__ == "__main__":
    main()
