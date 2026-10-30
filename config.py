import os

from dotenv import load_dotenv

load_dotenv()

# Страница уведомлений AnimeLib
URL = os.getenv("URL")
# Профиль браузера с сохранённой сессией (launch_persistent_context)
USER_DATA_DIR = os.getenv("USER_DATA_DIR")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///anitracker.db")

# Telegram-рассылка 
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Как часто проверять уведомления (минуты)
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))


def require_startup_settings() -> None:
    missing = [name for name in ("URL", "USER_DATA_DIR") if not globals()[name]]
    if missing:
        raise RuntimeError(
            f"Заполните в .env: {', '.join(missing)}"
        )
