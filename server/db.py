import hashlib
import os
import secrets
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(os.environ.get("ARENA_DB", Path(__file__).resolve().parent.parent / "arena.db"))

TIME_CONTROLS = {"blitz": 60, "rapid": 180, "classical": 300}
START_RATING = 800.0

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL COLLATE NOCASE,
  pw_hash TEXT NOT NULL,
  salt TEXT NOT NULL,
  lang TEXT NOT NULL DEFAULT 'en',
  new_per_day INTEGER NOT NULL DEFAULT 10,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS ratings (
  user_id INTEGER NOT NULL,
  tc TEXT NOT NULL,
  rating REAL NOT NULL,
  games INTEGER NOT NULL DEFAULT 0,
  wins INTEGER NOT NULL DEFAULT 0,
  losses INTEGER NOT NULL DEFAULT 0,
  draws INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, tc)
);
CREATE TABLE IF NOT EXISTS rating_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  tc TEXT NOT NULL,
  rating REAL NOT NULL,
  match_id TEXT,
  ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS matches (
  id TEXT PRIMARY KEY,
  tc TEXT NOT NULL,
  rated INTEGER NOT NULL,
  bot INTEGER NOT NULL,
  level TEXT NOT NULL,
  p1_id INTEGER NOT NULL,
  p2_id INTEGER,
  p2_name TEXT NOT NULL,
  p1_score INTEGER, p2_score INTEGER,
  p1_correct INTEGER, p1_wrong INTEGER,
  p2_correct INTEGER, p2_wrong INTEGER,
  result TEXT,
  p1_before REAL, p1_after REAL,
  p2_before REAL, p2_after REAL,
  started_at REAL NOT NULL,
  ended_at REAL,
  data TEXT
);
CREATE INDEX IF NOT EXISTS ix_matches_p1 ON matches(p1_id, ended_at);
CREATE INDEX IF NOT EXISTS ix_matches_p2 ON matches(p2_id, ended_at);
CREATE TABLE IF NOT EXISTS srs (
  user_id INTEGER NOT NULL,
  card_id INTEGER NOT NULL,
  state TEXT NOT NULL DEFAULT 'learning',
  step INTEGER NOT NULL DEFAULT 0,
  ease REAL NOT NULL DEFAULT 2.5,
  interval REAL NOT NULL DEFAULT 0,
  reps INTEGER NOT NULL DEFAULT 0,
  lapses INTEGER NOT NULL DEFAULT 0,
  due REAL NOT NULL,
  last REAL,
  source TEXT NOT NULL DEFAULT 'study',
  PRIMARY KEY (user_id, card_id)
);
CREATE TABLE IF NOT EXISTS study_daily (
  user_id INTEGER NOT NULL,
  day TEXT NOT NULL,
  new_count INTEGER NOT NULL DEFAULT 0,
  reviews INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);
"""


def connect():
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


con = connect()
con.executescript(SCHEMA)


def q(sql, *args):
    return con.execute(sql, args).fetchall()


def q1(sql, *args):
    return con.execute(sql, args).fetchone()


def ex(sql, *args):
    return con.execute(sql, args)


# ---------- auth ----------

def hash_pw(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()


def create_user(username: str, pw: str):
    salt = secrets.token_hex(16)
    cur = ex("INSERT INTO users (username, pw_hash, salt, created_at) VALUES (?,?,?,?)",
             username, hash_pw(pw, salt), salt, time.time())
    uid = cur.lastrowid
    for tc in TIME_CONTROLS:
        ex("INSERT INTO ratings (user_id, tc, rating) VALUES (?,?,?)", uid, tc, START_RATING)
    return uid


def check_login(username: str, pw: str):
    u = q1("SELECT * FROM users WHERE username=?", username)
    if not u or not secrets.compare_digest(u["pw_hash"], hash_pw(pw, u["salt"])):
        return None
    return u


def new_session(uid: int) -> str:
    tok = secrets.token_urlsafe(32)
    ex("INSERT INTO sessions (token, user_id, created_at) VALUES (?,?,?)", tok, uid, time.time())
    return tok


def user_from_token(tok):
    if not tok:
        return None
    return q1("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?", tok)


def ratings_for(uid: int) -> dict:
    return {r["tc"]: dict(r) for r in q("SELECT * FROM ratings WHERE user_id=?", uid)}
