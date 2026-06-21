import os
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "researchgpt.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            content TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            paper_id INTEGER,
            summary TEXT NOT NULL,
            style TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (paper_id) REFERENCES papers(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            paper_id INTEGER,
            message_type TEXT NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (paper_id) REFERENCES papers(id)
        )
        """
    )
    conn.commit()
    conn.close()


def create_user(username, password_hash):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True, cur.lastrowid
    except sqlite3.IntegrityError:
        return False, None
    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def save_uploaded_paper(user_id, file_name, content, file_path):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO papers (user_id, file_name, content, file_path, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, file_name, content, file_path, datetime.utcnow().isoformat()),
    )
    conn.commit()
    paper_id = cur.lastrowid
    conn.close()
    return paper_id


def get_uploaded_papers(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM papers WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_summary(user_id, paper_id, summary, style):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO summaries (user_id, paper_id, summary, style, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, paper_id, summary, style, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def save_chat_message(user_id, paper_id, message_type, prompt, response):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_history (user_id, paper_id, message_type, prompt, response, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, paper_id, message_type, prompt, response, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_chat_history(user_id, paper_id=None, limit=50):
    conn = get_connection()
    cur = conn.cursor()
    if paper_id is None:
        cur.execute(
            "SELECT * FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
    else:
        cur.execute(
            "SELECT * FROM chat_history WHERE user_id = ? AND paper_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, paper_id, limit),
        )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]