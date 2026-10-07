"""Почасовой дайджест для GitHub Actions (только stdlib, без aiogram).

Логика:
  1. Ищет свежие репы по QUERIES через GitHub Search API (sort=created).
  2. Отсекает старше LOOKBACK_HOURS и уже отправленные (seen.json в репозитории).
  3. Шлёт новинки в Telegram через sendMessage.
  4. Обновляет seen.json (workflow коммитит его обратно).

Переменные окружения (Secrets в GitHub):
  TELEGRAM_BOT_TOKEN, OWNER_CHAT_ID,
  optional: GITHUB_TOKEN (в Actions подставляется автоматически),
  LOOKBACK_HOURS=25, MAX_RESULTS_PER_QUERY=10, QUERY_DELAY_SEC=7,
  MANUAL_QUERY="" — если задан, ищет только этот запрос (топ-5, без seen.json).
"""
from __future__ import annotations

import explain
import html
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SEEN_FILE = BASE / "seen.json"
MAX_SEEN = 3000

QUERIES = [
    "LLM jailbreak",
    "AI jailbreak",
    "ChatGPT jailbreak",
    "Claude jailbreak prompt",
    "prompt injection bypass LLM",
    "uncensored LLM",
    "DAN prompt ChatGPT",
    "Gemini jailbreak bypass",
    "free ChatGPT API",
    "free OpenAI API",
    "free LLM API",
    "ChatGPT API free proxy",
    "free GPT-4 access",
    "free AI chatbot",
    "ChatGPT free account",
    "free AI tokens",
]

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["OWNER_CHAT_ID"]
GH_TOKEN = os.getenv("GITHUB_TOKEN", "")
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "25"))
PER_QUERY = int(os.getenv("MAX_RESULTS_PER_QUERY", "10"))
DELAY = float(os.getenv("QUERY_DELAY_SEC", "7"))
MANUAL_QUERY = os.getenv("MANUAL_QUERY", "").strip()


def load_seen() -> set[str]:
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")).get("urls", []))
        except Exception:
            pass
    return set()


def save_seen(seen: set[str]) -> None:
    SEEN_FILE.write_text(json.dumps({"urls": list(seen)[-MAX_SEEN:]}), encoding="utf-8")


def gh_search(query: str, created_after: str = "") -> list[dict]:
    # sort=created у GitHub search НЕ существует (молча игнорируется),
    # свежесть задаём квалификатором created:>YYYY-MM-DD
    q = f"{query} created:>{created_after}" if created_after else query
    params = urllib.parse.urlencode(
        {"q": q, "sort": "updated", "order": "desc", "per_page": PER_QUERY}
    )
    req = urllib.request.Request(
        f"https://api.github.com/search/repositories?{params}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ai-abuse-digest",
            **({"Authorization": f"Bearer {GH_TOKEN}"} if GH_TOKEN else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r).get("items", [])
    except Exception as e:
        print(f"GitHub query failed [{query}]: {e}")
        return []


def tg_send(text: str) -> None:
    payload = json.dumps(
        {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML",
         "disable_web_page_preview": True}
    ).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        json.load(r)


def fmt(repo: dict, query: str) -> str:
    name = html.escape(repo.get("full_name", "unknown"))
    desc = html.escape((repo.get("description") or "без описания")[:300])
    url = repo.get("html_url", "")
    stars = repo.get("stargazers_count", 0)
    lang = html.escape(repo.get("language") or "—")
    created = (repo.get("created_at") or "")[:10]
    q = html.escape(query)
    return (f"🚨 <b>{name}</b> ⭐ {stars}\n📝 {desc}\n"
            f"💻 {lang} | Создан: {created}\n🔎 <i>{q}</i>\n🔗 {url}\n"
            f"{explain.repo_ru(repo)}")


def main() -> None:
    if MANUAL_QUERY:
        manual_search(MANUAL_QUERY)
        return
    seen = load_seen()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    created_after = cutoff.strftime("%Y-%m-%d")
    fresh: list[tuple[dict, str]] = []
    batch: set[str] = set()

    for i, q in enumerate(QUERIES):
        if i:
            time.sleep(DELAY)
        for repo in gh_search(q, created_after):
            url = repo.get("html_url", "")
            if not url or url in seen or url in batch:
                continue
            try:
                created = datetime.fromisoformat(
                    repo.get("created_at", "").replace("Z", "+00:00"))
            except ValueError:
                continue
            if created < cutoff:
                continue
            batch.add(url)
            fresh.append((repo, q))

    fresh.sort(key=lambda t: t[0].get("created_at", ""), reverse=True)
    print(f"fresh repos: {len(fresh)}")

    sent = 0
    for repo, q in fresh[:10]:
        try:
            tg_send(fmt(repo, q))
        except Exception as e:
            print(f"send failed [{repo.get('html_url')}]: {e}")
            continue  # не помечаем как отправленное — попробуем в следующий раз
        seen.add(repo["html_url"])
        sent += 1
        time.sleep(1)

    # чистим хвост seen, чтобы файл не рос бесконечно
    save_seen(seen)
    print(f"sent: {sent}, seen total: {min(len(seen), MAX_SEEN)}")


def manual_search(query: str) -> None:
    """Ручной поиск по запросу из чата: топ-5 без фильтра даты, seen.json не трогаем."""
    items = gh_search(query)
    print(f"manual results: {len(items)}")
    if not items:
        tg_send(f"🔎 По запросу <i>{html.escape(query)}</i> ничего не нашлось.",
                )
    for repo in items[:5]:
        try:
            tg_send(fmt(repo, query))
        except Exception as e:
            print(f"send failed [{repo.get('html_url')}]: {e}")
        time.sleep(1)
    print("manual done (seen.json untouched)")


if __name__ == "__main__":
    main()
