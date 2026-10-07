"""ТГ-бот мониторинга свежих AI-джейлбрейков / обходов с GitHub.

Команды:
  /start      — помощь
  /subscribe  — подписаться на авто-дайджест
  /unsubscribe— отписаться
  /latest     — свежие находки за LOOKBACK_HOURS прямо сейчас
  /search <текст> — ручной поиск по GitHub (топ-5 по дате создания)
  /queries    — по каким запросам мониторим
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

import config
import github_monitor
import storage

logging.basicConfig(level=logging.INFO)
router = Router()


@router.message(Command("start"))
async def cmd_start(msg: Message):
    storage.add_subscriber(msg.chat.id)  # автоподписка: сразу шлём дайджесты сюда
    await msg.answer(
        "👋 Привет! Я мониторю GitHub и ищу <b>самые свежие AI-абузы</b>:\n"
        "джейлбрейки, обходы, prompt injection, uncensored LLM,\n"
        "а также халявные нейронки / бесплатные API / токены.\n\n"
        "✅ Ты уже подписан — новинки будут прилетать сюда сами.\n\n"
        "Команды:\n"
        "/unsubscribe — отписаться\n"
        "/latest — что нашлось за последние 24ч\n"
        "/search <code>запрос</code> — ручной поиск\n"
        "/queries — текущие поисковые запросы",
        parse_mode="HTML",
    )


@router.message(Command("subscribe"))
async def cmd_sub(msg: Message):
    storage.add_subscriber(msg.chat.id)
    await msg.answer("✅ Подписал! Буду присылать свежие находки сюда.")


@router.message(Command("unsubscribe"))
async def cmd_unsub(msg: Message):
    storage.remove_subscriber(msg.chat.id)
    await msg.answer("❌ Отписал. /subscribe — чтобы вернуть.")


@router.message(Command("queries"))
async def cmd_queries(msg: Message):
    lines = "\n".join(f"• <code>{q}</code>" for q in config.DEFAULT_QUERIES)
    await msg.answer(
        f"🔎 Мониторю запросы (каждые {config.CHECK_INTERVAL_MINUTES} мин):\n{lines}",
        parse_mode="HTML",
    )


@router.message(Command("latest"))
async def cmd_latest(msg: Message):
    wait = await msg.answer("⏳ Ищу свежее на GitHub...")
    repos = await github_monitor.fetch_fresh()
    new = [r for r in repos if not storage.is_seen(r["html_url"])]
    if not new:
        await wait.edit_text("Пока тихо — ничего нового за последние "
                             f"{config.LOOKBACK_HOURS}ч. Попробуй /search jailbreak")
        return
    storage.mark_seen([r["html_url"] for r in new])
    await wait.delete()
    for repo in new[:10]:
        await msg.answer(github_monitor.format_repo(repo), parse_mode="HTML",
                         disable_web_page_preview=True)
        await asyncio.sleep(0.3)


@router.message(Command("search"))
async def cmd_search(msg: Message):
    parts = (msg.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Использование: <code>/search ChatGPT DAN bypass</code>", parse_mode="HTML")
        return
    query = parts[1].strip()
    wait = await msg.answer(f"⏳ Ищу: <i>{query}</i>...", parse_mode="HTML")
    repos = await github_monitor.search_repos(query, per_page=5)
    if not repos:
        await wait.edit_text("Ничего не нашёл (или упёрлись в лимит GitHub API).")
        return
    await wait.delete()
    for repo in repos:
        repo["_matched_query"] = query
        await msg.answer(github_monitor.format_repo(repo), parse_mode="HTML",
                         disable_web_page_preview=True)
        await asyncio.sleep(0.3)


async def monitor_loop(bot: Bot):
    """Фоновая задача: раз в CHECK_INTERVAL_MINUTES рассылает новинки подписчикам."""
    while True:
        try:
            repos = await github_monitor.fetch_fresh()
            fresh = [r for r in repos if not storage.is_seen(r["html_url"])]
            if fresh:
                storage.mark_seen([r["html_url"] for r in fresh])
                subs = storage.get_subscribers()
                for chat_id in subs:
                    for repo in fresh[:10]:
                        try:
                            await bot.send_message(
                                chat_id, github_monitor.format_repo(repo),
                                parse_mode="HTML", disable_web_page_preview=True,
                            )
                            await asyncio.sleep(0.3)
                        except Exception as e:
                            logging.warning("Не смог отправить %s: %s", chat_id, e)
            logging.info("Проверка done: всего=%d новых=%d подписчиков=%d",
                         len(repos), len(fresh) if 'fresh' in locals() else 0,
                         len(storage.get_subscribers()))
        except Exception as e:
            logging.exception("Ошибка в monitor_loop: %s", e)
        await asyncio.sleep(config.CHECK_INTERVAL_MINUTES * 60)


async def main():
    if not config.TELEGRAM_BOT_TOKEN or "ВСТАВЬ" in config.TELEGRAM_BOT_TOKEN:
        raise SystemExit(
            "❌ Нет TELEGRAM_BOT_TOKEN.\n"
            "1) Напиши @BotFather в Telegram -> /newbot -> скопируй токен\n"
            "2) Скопируй .env.example в .env и вставь токен\n"
            "3) Запусти снова: python bot.py"
        )
    storage.init_db()
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    asyncio.create_task(monitor_loop(bot))
    logging.info("Бот запущен. Мониторю каждые %d мин.", config.CHECK_INTERVAL_MINUTES)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
