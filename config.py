import os
import re
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(os.path.abspath(__file__)).parent
INSTANCE_DIR = BASE_DIR / "instance"
DEFAULT_DB_FILE = INSTANCE_DIR / "BrewScout.db"

load_dotenv(BASE_DIR / ".env")


def sqlite_uri_for(path) -> str:
    return "sqlite:///" + Path(os.path.abspath(path)).as_posix()


def resolve_database_uri() -> str:
    raw = os.getenv("DATABASE_URL", "").strip().strip("'\"")

    if not raw:
        DEFAULT_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        return sqlite_uri_for(DEFAULT_DB_FILE)

    # Convert standard postgres URIs to use the installed psycopg2 driver
    if raw.startswith("postgres://"):
        return "postgresql+psycopg2://" + raw[len("postgres://"):]

    if raw.startswith("postgresql://") and not raw.startswith("postgresql+"):
        return "postgresql+psycopg2://" + raw[len("postgresql://"):]

    if raw.startswith("sqlite:///"):
        db_part, _, query = raw[len("sqlite:///"):].partition("?")
        if db_part in ("", ":memory:"):
            return raw
        if re.match(r"^/[A-Za-z]:[/\\]", db_part):
            db_part = db_part[1:]
        db_file = Path(db_part)
        if not db_file.is_absolute():
            db_file = BASE_DIR / db_file
        db_file = Path(os.path.abspath(db_file))
        db_file.parent.mkdir(parents=True, exist_ok=True)
        return sqlite_uri_for(db_file) + (f"?{query}" if query else "")

    return raw


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "brew-scout-cafe-wifi-finder-key-2026")
    SQLALCHEMY_DATABASE_URI = resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Admin Credentials
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "anthonyomokpo6489@gmail.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "12345678")

    # Production Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    if SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"timeout": 30}}

    WTF_CSRF_ENABLED = True