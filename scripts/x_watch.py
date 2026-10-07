"""Мониторинг X/Twitter через официальный API v2 (recent search).

Честно: бесплатный тариф X API поиск НЕ отдаёт (только постинг).
Модуль активируется при секрете X_BEARER_TOKEN с тарифом Basic и выше.
Без токена — тихо пропускается, остальной дайджест работает как раньше.
"""
from __future__ import annotations

import html
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import digest  # tg_send, load_seen, save_seen
import explain

X_TOKEN = os.getenv("X_BEARER_TOKEN", "")

X_QUERIES = [
    "LLM jailbreak -is:retweet",
    "ChatGPT jailbreak -is:retweet",
    "prompt injection bypass AI -is:retweet",
    "uncensored LLM -is:retweet",
    "free ChatGPT API -is:retweet",
    "free GPT-4 -is:retweet",
]


def x_search(query: str) -> tuple[list[dict], dict[str, str]]:
    params = urllib.parse.urlencode({
        "query": query,
        "max_results": 10,
        "tweet.fields": "created_at,public_metrics",
        "expansions": "author_id",
        "user.fields": "username",
    })
    req = urllib.request.Request(
        "https://api.twitter.com/2/tweets/search/recent?" + params,
        headers={"Authorization": f"Bearer {X_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    users = {u["id"]: u.get("username", "?")
             for u in data.get("includes", {}).get("users", [])}
    return data.get("data", []), users


def fmt_tweet(tw: dict, username: str, query: str) -> str:
    tid = tw["id"]
    text = html.escape((tw.get("text", "") or "")[:300])
    m = tw.get("public_metrics", {}) or {}
    url = f"https://x.com/{username}/status/{tid}" if username != "?" else f"https://x.com/i/status/{tid}"
    return (f"🐦 <b>@{html.escape(username)}</b> "
            f"❤️ {m.get('like_count', 0)} 🔁 {m.get('retweet_count', 0)}\n"
            f"📝 {text}\n🔎 <i>{html.escape(query)}</i>\n🔗 {url}\n"
            f"{explain.tweet_ru(tw.get('text', ''), m.get('like_count', 0), m.get('retweet_count', 0))}")


def main() -> None:
    if not X_TOKEN:
        print("x_watch: no X_BEARER_TOKEN — skipped (дайджест GitHub идёт по плану)")
        return
    seen = digest.load_seen()
    fresh: list[tuple[dict, str, str]] = []
    batch: set[str] = set()
    for i, q in enumerate(X_QUERIES):
        if i:
            time.sleep(3)
        try:
            tweets, users = x_search(q)
        except Exception as e:
            print(f"X query failed [{q}]: {e}")
            continue
        for tw in tweets:
            key = f"x:{tw['id']}"
            if key in seen or key in batch:
                continue
            batch.add(key)
            fresh.append((tw, users.get(tw.get("author_id", ""), "?"), q))

    print(f"x fresh: {len(fresh)}")
    sent = 0
    for tw, username, q in fresh[:10]:
        try:
            digest.tg_send(fmt_tweet(tw, username, q))
        except Exception as e:
            print(f"x send failed [{tw['id']}]: {e}")
            continue
        seen.add(f"x:{tw['id']}")
        sent += 1
        time.sleep(1)
    digest.save_seen(seen)
    print(f"x sent: {sent}")


if __name__ == "__main__":
    main()
