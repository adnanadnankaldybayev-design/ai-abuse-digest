"""Объяснения находок на русском. Только stdlib, без внешних API.

Классифицирует по ключевым словам в названии/описании/тексте и выдаёт
короткое объяснение: что это и чем интересно. Без гаданий — если категория
неясна, так и пишем.
"""
from __future__ import annotations

RULES: list[tuple[str, tuple[str, ...], str]] = [
    ("🔓 Джейлбрейк",
     ("jailbreak", "jail-break", "dan prompt", "dan mode", "bypass", "обход",
      "unlock gpt", "unlock chatgpt", "evil prompt"),
     "способ снять ограничения нейросети: заставляет отвечать на то, что обычно запрещено."),
    ("💉 Промпт-инъекция",
     ("prompt injection", "prompt-injection", "injection attack", "инъекция",
      "ignore previous", "ignore all previous", "system prompt leak"),
     "атака через хитрый запрос: перехват системного промпта или навязывание модели чужих инструкций."),
    ("🚫 Uncensored-модель",
     ("uncensored", "unfiltered", "without censorship", "без цензуры", "nsfw model"),
     "модель без встроенных запретов — отвечает на всё подряд, включая жесть."),
    ("🎁 Халявный API/доступ",
     ("free api", "free gpt", "gpt free", "free chatgpt", "api free", "free key",
      "free tokens", "бесплатный api", "халяв", "proxy", "gpt-4 free", "gpt4 free"),
     "бесплатный доступ к нейронке: прокси, раздаваемые ключи или обёртка над чужим API."),
    ("👤 Аккаунты/ключи",
     ("free account", "accounts", "аккаунт", "cookies", "session", "plus account"),
     "раздача аккаунтов/сессий: забираешь чужой доступ к платной нейронке."),
    ("🎭 Дипфейк/войс",
     ("deepfake", "дипфейк", "voice clone", "клонирование голоса", "face swap",
      "talking head", "voice changer"),
     "подделка голоса/лица: клонирование голоса или замена лица на видео."),
    ("⚠️ Вредоносное",
     ("stealer", "malware", "phishing", "фишинг", "rat ", "keylogger", "botnet",
      "ransomware", "crack password"),
     "вредоносный инструмент: кража данных, фишинг или взлом. Осторожно."),
]

DEFAULT = ("🆕 Находка по теме ИИ",
           "свежий репозиторий/пост про нейросети из мониторинга. Смотри описание и ссылку.")


def classify(text: str) -> tuple[str, str]:
    t = (text or "").lower()
    for title, keywords, meaning in RULES:
        if any(k in t for k in keywords):
            return title, meaning
    return DEFAULT


def repo_ru(repo: dict) -> str:
    """Строка объяснения для карточки репозитория."""
    title, meaning = classify(
        f"{repo.get('full_name', '')} {repo.get('description', '')} "
        f"{' '.join(repo.get('topics', []) or [])}"
    )
    stars = repo.get("stargazers_count", 0) or 0
    if stars >= 500:
        hype = "Народ уже заметил (звёзд много) — стоящая штука."
    elif stars >= 50:
        hype = "Набирает звёзды — стоит глянуть."
    else:
        hype = "Пока малоизвестный — ты среди первых."
    return f"🇷🇺 {title} — {meaning} {hype}"


def tweet_ru(text: str, likes: int = 0, reposts: int = 0) -> str:
    """Строка объяснения для твита."""
    title, meaning = classify(text)
    buzz = likes + reposts
    if buzz >= 1000:
        hype = "Пост завирусился — обсуждают все."
    elif buzz >= 100:
        hype = "Пост набирает охват."
    else:
        hype = "Свежий пост, пока тихо."
    return f"🇷🇺 {title} — {meaning} {hype}"
