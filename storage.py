"""Хранилище: подписчики + уже отправленные репозитории. Только stdlib sqlite3."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).with_name("bot_data.db")


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.execute(
        "CREATE TABLE IF NOT EXISTS subscribers (chat_id INTEGER PRIMARY KEY, created_at REAL)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS seen_repos (url TEXT PRIMARY KEY, sent_at REAL)"
    )
    return c


def init_db() -> None:
    with _conn() as c:
        pass  # таблицы создаются в _conn()


def add_subscriber(chat_id: int) -> None:
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO subscribers (chat_id, created_at) VALUES (?, ?)",
            (chat_id, time.time()),
        )


def remove_subscriber(chat_id: int) -> None:
    with _conn() as c:
        c.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))


def get_subscribers() -> list[int]:
    with _conn() as c:
        return [r[0] for r in c.execute("SELECT chat_id FROM subscribers")]


def is_seen(url: str) -> bool:
    with _conn() as c:
        return c.execute("SELECT 1 FROM seen_repos WHERE url = ?", (url,)).fetchone() is not None


def mark_seen(urls: list[str]) -> None:
    now = time.time()
    with _conn() as c:
        c.executemany(
            "INSERT OR IGNORE INTO seen_repos (url, sent_at) VALUES (?, ?)",
            [(u, now) for u in urls],
        )
