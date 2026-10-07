# AI Abuse Monitor Bot 🤖🚨

Телеграм-бот, который мониторит GitHub и присылает **самые свежие AI-джейлбрейки / обходы**:
`LLM jailbreak`, `prompt injection bypass`, `uncensored LLM`, `DAN prompt` и т.д.

## Как запустить за 3 минуты

1. Создай бота:
   - Напиши [@BotFather](https://t.me/BotFather) → `/newbot` → скопируй токен вида `123456:ABC-...`

2. Установи зависимости:
```powershell
cd ai_abuse_monitor_bot
pip install -r requirements.txt
```

3. Настрой:
```powershell
Copy-Item .env.example .env
# открой .env и вставь TELEGRAM_BOT_TOKEN
# GITHUB_TOKEN — необязательно, но без него лимит GitHub 60 запросов/час
# взять тут: https://github.com/settings/tokens (достаточно public read-only)
```

4. Запусти:
```powershell
python bot.py
```

5. В Telegram:
   - найди своего бота → `/start` → `/subscribe`
   - раз в час (по умолчанию) будут приходить новинки
   - `/latest` — проверить прямо сейчас
   - `/search Claude jailbreak` — ручной поиск

## Настройки (.env)

| Переменная | По умолчанию | Что значит |
|---|---|---|
| `CHECK_INTERVAL_MINUTES` | 60 | как часто проверять GitHub |
| `LOOKBACK_HOURS` | 24 | считать "свежим" за последние N часов |
| `MAX_RESULTS_PER_QUERY` | 10 | сколько брать с каждого запроса |

Поисковые запросы меняются в `config.py` → `DEFAULT_QUERIES`.

## Как это работает

- `bot.py` — Telegram (aiogram 3), команды + фоновая рассылка
- `github_monitor.py` — `GET /search/repositories?q=...&sort=created&order=desc`, фильтр по дате
- `storage.py` — sqlite `bot_data.db`: подписчики + уже отправленные URL (без дублей)
