"""Database schema — CREATE TABLE statements and initial migration."""

from __future__ import annotations

import logging

from thelocaltutor.infrastructure.database.connection import get_connection

log = logging.getLogger(__name__)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS materials (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    file_path       TEXT    NOT NULL UNIQUE,
    file_type       TEXT    NOT NULL,
    date_added      TEXT    NOT NULL,
    page_count      INTEGER NOT NULL DEFAULT 0,
    status          TEXT    NOT NULL DEFAULT 'pending',
    course          TEXT    NOT NULL DEFAULT '',
    error_message   TEXT    NOT NULL DEFAULT '',
    chunk_count     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id     INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    page_number     INTEGER NOT NULL,
    chunk_index     INTEGER NOT NULL,
    content         TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id     INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    question_type   TEXT    NOT NULL,
    difficulty      TEXT    NOT NULL DEFAULT 'medium',
    question_text   TEXT    NOT NULL,
    correct_answer  TEXT    NOT NULL,
    explanation     TEXT    NOT NULL DEFAULT '',
    topic           TEXT    NOT NULL DEFAULT '',
    source_page     INTEGER NOT NULL DEFAULT 0,
    date_created    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS question_options (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id     INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    letter          TEXT    NOT NULL,
    option_text     TEXT    NOT NULL,
    is_correct      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS study_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id     INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    mode            TEXT    NOT NULL DEFAULT 'practice',
    started_at      TEXT    NOT NULL,
    ended_at        TEXT,
    total_questions INTEGER NOT NULL DEFAULT 0,
    correct_count   INTEGER NOT NULL DEFAULT 0,
    score_percent   REAL
);

CREATE TABLE IF NOT EXISTS session_questions (
    session_id      INTEGER NOT NULL REFERENCES study_sessions(id) ON DELETE CASCADE,
    question_id     INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    position        INTEGER NOT NULL,
    PRIMARY KEY (session_id, question_id)
);

CREATE TABLE IF NOT EXISTS attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES study_sessions(id) ON DELETE CASCADE,
    question_id     INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    user_answer     TEXT    NOT NULL,
    is_correct      INTEGER NOT NULL DEFAULT 0,
    time_taken_seconds INTEGER NOT NULL DEFAULT 0,
    timestamp       TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_questions_material ON questions(material_id);
CREATE INDEX IF NOT EXISTS idx_chunks_material    ON document_chunks(material_id);
CREATE INDEX IF NOT EXISTS idx_attempts_session   ON attempts(session_id);
"""


def initialise() -> None:
    conn = get_connection()
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    log.info("Database schema initialised")
