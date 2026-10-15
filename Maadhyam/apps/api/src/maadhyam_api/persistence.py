"""SQLite persistence for fictional prototype records only."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DB_PATH = Path(os.getenv('MAADHYAM_DB_PATH', './maadhyam-demo.sqlite3'))


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA busy_timeout=10000')
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('''CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY, service TEXT NOT NULL, kind TEXT NOT NULL,
            status TEXT NOT NULL, payload TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1)''')
        db.execute('''CREATE TABLE IF NOT EXISTS application_events (
            id TEXT PRIMARY KEY, application_id TEXT NOT NULL,
            event TEXT NOT NULL, timestamp TEXT NOT NULL,
            FOREIGN KEY(application_id) REFERENCES applications(id))''')
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def record_event(db, application_id, event):
    db.execute('INSERT INTO application_events VALUES (?,?,?,?)', (str(uuid4()), application_id, event, now()))


def decode(row):
    result = dict(row)
    result['payload'] = json.loads(result['payload'])
    return result
