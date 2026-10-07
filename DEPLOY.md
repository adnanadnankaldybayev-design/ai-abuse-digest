# Деплой 24/7 БЕСПЛАТНО через GitHub Actions

Боту не нужен постоянно включённый ПК: каждый час GitHub сам запускает
`scripts/digest.py`, ищет свежие репы и шлёт тебе в Telegram. Бесплатно.

## Что нужно от тебя (5 минут)

**Шаг 1. Нажми `/start` в `@watermelonsforabuz_bot`** и напиши мне «старт нажал» —
я узнаю твой chat_id (нужен для отправки).

**Шаг 2. Создай репозиторий на GitHub:**
- https://github.com/new → имя напр. `ai-abuse-digest` → **Public** → Create
- На странице репозитория: `Add file` → `Upload files` → перетащи **всё содержимое**
  папки `ai_abuse_monitor_bot` (включая `.github`, `scripts`, `seen.json`) → Commit

**Шаг 3. Добавь секреты:** в репозитории `Settings` → `Secrets and variables` → `Actions` → `New repository secret`:
| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | `8689810001:AAGsE0hsbJ32BtRt1RiaAOyDh4PFOsO7KOo` |
| `OWNER_CHAT_ID` | пришлю после шага 1 |

**Шаг 4. Запусти вручную первый раз:** вкладка `Actions` → `ai-abuse-digest` →
`Run workflow`. Если в личку прилетел дайджест — всё работает, дальше само каждый час.

**Шаг 5.** Скажи мне «actions работает» — я остановлю бота на этом ПК,
чтобы не было дублей.

## Важно

- Расписание: каждый час (`cron: "17 * * * *"` в `.github/workflows/digest.yml`).
- Дедупликация: отправленное запоминается в `seen.json` (коммитится автоматически).
- Лимиты GitHub API в Actions выше, чем без токена, — хватает с запасом.
- Если захочешь потом VPS вместо Actions — `Dockerfile` + `docker-compose.yml` уже лежат в папке.

## Альтернатива: дешёвый VPS (~150–300 ₽/мес)

1. Купи VPS с Ubuntu (Timeweb / AEZA / Selectel).
2. Там: `apt install docker.io docker-compose-plugin`, скопируй папку бота,
   положи `.env`, запусти `docker compose up -d`.
