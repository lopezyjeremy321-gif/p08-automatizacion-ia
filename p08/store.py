"""Adaptador local (SQLite) que hace de 'hoja de tareas de prueba' + outbox simulada."""
from __future__ import annotations

import csv
import io
import sqlite3
import threading
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks(
  id TEXT PRIMARY KEY, message_id TEXT UNIQUE NOT NULL,
  from_email TEXT NOT NULL, from_name TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL,
  label TEXT NOT NULL, confidence REAL NOT NULL, provider TEXT NOT NULL,
  title TEXT NOT NULL, priority TEXT NOT NULL, due_date TEXT,
  status TEXT NOT NULL, flags TEXT NOT NULL DEFAULT '',
  draft_subject TEXT, draft_body TEXT, draft_version INTEGER NOT NULL DEFAULT 0,
  created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS approvals(
  id TEXT PRIMARY KEY, task_id TEXT NOT NULL, draft_hash TEXT NOT NULL, recipient TEXT NOT NULL,
  expires_at REAL NOT NULL, status TEXT NOT NULL, created_at REAL NOT NULL, decided_by TEXT);
CREATE TABLE IF NOT EXISTS outbox(
  id INTEGER PRIMARY KEY AUTOINCREMENT, approval_id TEXT UNIQUE NOT NULL,
  recipient TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL, sent_at REAL NOT NULL, mode TEXT NOT NULL);
"""

_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


class Store:
    def __init__(self, path: str = ":memory:"):
        self._db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self._db.executescript(SCHEMA)

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            return self._db.execute(sql, params)

    def one(self, sql: str, params: tuple = ()):
        with self._lock:
            return self._db.execute(sql, params).fetchone()

    def all(self, sql: str, params: tuple = ()):
        with self._lock:
            return self._db.execute(sql, params).fetchall()

    def count_sent(self) -> int:
        return self.one("SELECT COUNT(*) c FROM outbox")["c"]

    def purge_older_than(self, days: int, now: float | None = None) -> int:
        """Retencion limitada: borra tareas antiguas (y sus aprobaciones)."""
        cutoff = (now or time.time()) - days * 86400
        ids = [r["id"] for r in self.all("SELECT id FROM tasks WHERE created_at < ?", (cutoff,))]
        for i in ids:
            self.execute("DELETE FROM approvals WHERE task_id=?", (i,))
            self.execute("DELETE FROM tasks WHERE id=?", (i,))
        return len(ids)

    def export_csv(self) -> str:
        """Hoja de tareas: neutraliza formulas (= + - @) para abrir en Excel/Sheets."""
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["id", "titulo", "etiqueta", "prioridad", "vence", "estado"])
        for r in self.all("SELECT id,title,label,priority,due_date,status FROM tasks ORDER BY created_at"):
            row = [r["id"], r["title"], r["label"], r["priority"], r["due_date"] or "", r["status"]]
            w.writerow([("'" + c) if isinstance(c, str) and c.startswith(_FORMULA_START) else c for c in row])
        return out.getvalue()
