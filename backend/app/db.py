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
    summary_upto INTEGER NOT NULL DEFAULT 0,
    report_json TEXT,
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
DROP TABLE IF EXISTS lesson_bank;
CREATE TABLE IF NOT EXISTS exercise_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id TEXT NOT NULL,
    exercise_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('lesson', 'review')),
    run_id INTEGER,
    answer TEXT NOT NULL,
    correct INTEGER NOT NULL,
    seconds INTEGER NOT NULL DEFAULT 0,
    day TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_lesson_attempt ON exercise_attempts (module_id, exercise_id) WHERE kind = 'lesson';
CREATE UNIQUE INDEX IF NOT EXISTS ux_review_attempt ON exercise_attempts (run_id, exercise_id) WHERE kind = 'review';
CREATE TABLE IF NOT EXISTS review_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id TEXT NOT NULL,
    exercise_ids TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    score INTEGER
);
CREATE TABLE IF NOT EXISTS exam_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    question_ids TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    score INTEGER,
    passed INTEGER
);
CREATE TABLE IF NOT EXISTS exam_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES exam_runs(id),
    question_id TEXT NOT NULL,
    answer TEXT NOT NULL,
    correct INTEGER NOT NULL,
    seconds INTEGER NOT NULL DEFAULT 0,
    day TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (run_id, question_id)
);
CREATE TABLE IF NOT EXISTS exercise_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id TEXT NOT NULL,
    exercise_id TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL
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
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    sentence TEXT NOT NULL DEFAULT '',
    translation TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    UNIQUE (word, sentence)
);
CREATE TABLE IF NOT EXISTS call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    source TEXT NOT NULL,
    minutes INTEGER NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    link TEXT,
    lyrics TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 0,
    grammar_status TEXT NOT NULL DEFAULT 'pending' CHECK (grammar_status IN ('pending', 'done')),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS song_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    text TEXT NOT NULL,
    repeat_of INTEGER,
    highlights TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS song_practice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER REFERENCES song_chunks(id) ON DELETE CASCADE,
    song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('dictation', 'shadow', 'final')),
    text TEXT NOT NULL,
    score INTEGER NOT NULL,
    day TEXT NOT NULL,
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
