"""Run `python check_db.py` from the BrewScout folder.

Shows the database path BrewScout will really use, and tests each step that
can make SQLite say "unable to open database file". Needs no Flask code.
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

from dotenv import dotenv_values

import config

PREFIX = "sqlite:///"


def line(ok, label, detail=""):
    print(f"[{'OK' if ok else 'FAIL'}] {label}" + (f" -> {detail}" if detail else ""))
    return ok


def main():
    print(f"Python      : {sys.executable} ({sys.version.split()[0]})")
    print(f"Working dir : {os.getcwd()}")
    print(f"Project dir : {config.BASE_DIR}")

    env_url = os.environ.get("DATABASE_URL")
    dotenv_url = dotenv_values(config.BASE_DIR / ".env").get("DATABASE_URL")
    print(f"DATABASE_URL in environment : {env_url!r}")
    print(f"DATABASE_URL in .env file   : {dotenv_url!r}")
    if env_url or dotenv_url:
        print("  ^ This overrides the default instance/BrewScout.db location. "
              "Delete it (or fix it) unless you set it on purpose.")

    uri = config.Config.SQLALCHEMY_DATABASE_URI
    print(f"Resolved URI: {uri}")
    if not uri.startswith(PREFIX):
        print("Not a SQLite URL, nothing more to check here.")
        return 0

    db_file = Path(uri[len(PREFIX):].partition("?")[0])
    folder = db_file.parent
    ok = line(db_file.is_absolute(), "Database path is absolute", str(db_file))
    ok &= line(folder.is_dir(), "Folder exists", str(folder))

    try:
        with tempfile.NamedTemporaryFile(dir=folder, prefix="probe_", delete=True):
            pass
        ok &= line(True, "Folder is writable")
    except OSError as exc:
        ok &= line(False, "Folder is writable", f"{exc}  (check permissions / Windows "
                   "'Controlled folder access' / antivirus)")

    try:
        conn = sqlite3.connect(str(db_file), timeout=5)
        conn.execute("CREATE TABLE IF NOT EXISTS _probe (id INTEGER)")
        conn.execute("DROP TABLE _probe")
        conn.commit()
        conn.close()
        ok &= line(True, "sqlite3 can open and write the database file")
    except sqlite3.Error as exc:
        ok &= line(False, "sqlite3 can open and write the database file", str(exc))

    for suffix in ("-journal", "-wal", "-shm"):
        leftover = Path(str(db_file) + suffix)
        if leftover.exists():
            print(f"[WARN] Leftover {leftover.name} found - another program may still "
                  "have the database open (DB Browser, PyCharm Database tool).")

    print("\nAll checks passed - run `python seed.py`." if ok else
          "\nFix the first FAIL above, then run this again.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())