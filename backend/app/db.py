import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    module_id TEXT,
    topic TEXT,
    started_at TEXT NOT NULL,
    duration_s INTEGER,
    listening_score INTEGER,
    conversation_score INTEGER,
    final_score INTEGER,
    finished_at TEXT,
    day TEXT,
    summary TEXT,
    is_finished INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    audio_path TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mistakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    module_id TEXT,
    said TEXT NOT NULL,
    corrected TEXT NOT NULL,
    explanation TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
    module_id TEXT PRIMARY KEY,
    next_due TEXT NOT NULL,
    interval_days INTEGER NOT NULL,
    ease REAL NOT NULL,
    repetitions INTEGER NOT NULL,
    last_score INTEGER
);
CREATE TABLE IF NOT EXISTS listening_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    kind TEXT NOT NULL,
    prompt TEXT NOT NULL,
    audio_text TEXT NOT NULL,
    audio_path TEXT,
    options TEXT,
    answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    user_answer TEXT,
    correct INTEGER
);
CREATE TABLE IF NOT EXISTS media_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    episode TEXT,
    minutes INTEGER NOT NULL,
    pages INTEGER,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    kind TEXT NOT NULL,
    input_units INTEGER NOT NULL DEFAULT 0,
    output_units INTEGER NOT NULL DEFAULT 0,
    cost_brl REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
"""


def connect(path: str) -> sqlite3.Connection:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def insert(conn: sqlite3.Connection, table: str, **cols) -> int:
    names = ", ".join(cols)
    marks = ", ".join("?" for _ in cols)
    cur = conn.execute(f"INSERT INTO {table} ({names}) VALUES ({marks})", tuple(cols.values()))
    conn.commit()
    return cur.lastrowid
