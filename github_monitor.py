"""Поиск свежих репозиториев через GitHub REST API: GET /search/repositories"""
from __future__ import annotations

import asyncio
import html
from datetime import datetime, timedelta, timezone

import aiohttp

import config


def _headers() -> dict:
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-abuse-monitor-bot",
    }
    if config.GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    return h


async def search_repos(query: str, per_page: int = 10,
                     created_after: str | None = None) -> list[dict]:
    """Один запрос к GitHub.

    ВАЖНО: у search/repositories нет сортировки sort=created (игнорируется),
    поэтому свежесть задаём квалификатором created:>YYYY-MM-DD — это точный фильтр.
    """
    q = f"{query} created:>{created_after}" if created_after else query
    params = {
        "q": q,
        "sort": "updated",
        "order": "desc",
        "per_page": per_page,
    }
    async with aiohttp.ClientSession(headers=_headers()) as s:
        async with s.get(config.GITHUB_API, params=params, timeout=30) as r:
            if r.status == 403:
                # rate limit — возвращаем пусто, чтобы не ронять цикл
                return []
            r.raise_for_status()
            data = await r.json()
            return data.get("items", [])


async def fetch_fresh(since_hours: int | None = None) -> list[dict]:
    """Проходит по всем DEFAULT_QUERIES, отбирает репы моложе since_hours, дедуплицирует."""
    since_hours = since_hours if since_hours is not None else config.LOOKBACK_HOURS
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    created_after = cutoff.strftime("%Y-%m-%d")

    seen_urls: set[str] = set()
    fresh: list[dict] = []

    for i, q in enumerate(config.DEFAULT_QUERIES):
        if i > 0:
            await asyncio.sleep(config.GITHUB_QUERY_DELAY_SEC)  # не упираемся в rate limit
        try:
            items = await search_repos(q, per_page=config.MAX_RESULTS_PER_QUERY,
                                       created_after=created_after)
        except Exception:
            continue  # один упавший запрос не должен останавливать весь обход
        for repo in items:
            url = repo.get("html_url", "")
            if not url or url in seen_urls:
                continue
            created_raw = repo.get("created_at", "")
            try:
                created = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if created < cutoff:
                continue
            repo["_matched_query"] = q
            seen_urls.add(url)
            fresh.append(repo)

    fresh.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return fresh


def format_repo(repo: dict) -> str:
    """Карточка репозитория для Telegram (HTML)."""
    name = html.escape(repo.get("full_name", "unknown"))
    desc = html.escape((repo.get("description") or "без описания")[:300])
    url = repo.get("html_url", "")
    stars = repo.get("stargazers_count", 0)
    lang = html.escape(repo.get("language") or "—")
    created = (repo.get("created_at") or "")[:10]
    pushed = (repo.get("pushed_at") or "")[:10]
    query = html.escape(repo.get("_matched_query", ""))

    return (
        f"🚨 <b>{name}</b> ⭐ {stars}\n"
        f"📝 {desc}\n"
        f"💻 Язык: {lang} | Создан: {created} | Обновлён: {pushed}\n"
        f"🔎 Запрос: <i>{query}</i>\n"
        f"🔗 {url}"
    )
