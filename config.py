"""Конфиг бота. Все секреты — только из переменных окружения / .env"""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "ВСТАВЬ_ТОКЕН_ОТ_BOTFATHER")
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")  # необязательно, но поднимает лимит 60 -> 5000 req/час

CHECK_INTERVAL_MINUTES: int = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))
LOOKBACK_HOURS: int = int(os.getenv("LOOKBACK_HOURS", "24"))
MAX_RESULTS_PER_QUERY: int = int(os.getenv("MAX_RESULTS_PER_QUERY", "10"))

# Что мониторим:
# 1) джейлбрейки / обходы / промпт-инъекции / uncensored-модели
# 2) халявные нейронки: бесплатные API-прокси, обёртки, ключи, аккаунты
# Бот шлёт только карточки публичных репозиториев (название/описание/ссылка).
DEFAULT_QUERIES: list[str] = [
    # --- абузы / обходы ---
    "LLM jailbreak",
    "AI jailbreak",
    "ChatGPT jailbreak",
    "Claude jailbreak prompt",
    "prompt injection bypass LLM",
    "uncensored LLM",
    "DAN prompt ChatGPT",
    "Gemini jailbreak bypass",
    # --- халявные нейронки / токены / API ---
    "free ChatGPT API",
    "free OpenAI API",
    "free LLM API",
    "ChatGPT API free proxy",
    "free GPT-4 access",
    "free AI chatbot",
    "ChatGPT free account",
    "free AI tokens",
]

# Пауза между запросами к GitHub (сек). Без GITHUB_TOKEN лимит поиска ~10 запр/мин.
GITHUB_QUERY_DELAY_SEC: float = float(os.getenv("GITHUB_QUERY_DELAY_SEC", "7"))

GITHUB_API = "https://api.github.com/search/repositories"
