import logging
import os
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

import config
import tracker

LOCK_FILE = "anitracker.lock"
LOG_FILE = "anitracker.log"


def _acquire_lock() -> None:
    """Защита от двух одновременно запущенных копий демона."""
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        sys.exit("Демон уже запущен (найден anitracker.lock)")


def _release_lock() -> None:
    try:
        os.remove(LOCK_FILE)
    except FileNotFoundError:
        pass


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def run_check() -> None:
    try:
        tracker.check_once(config.URL, config.USER_DATA_DIR)
    except Exception:
        logging.getLogger(__name__).exception("Проверка завершилась с ошибкой")


def main() -> None:
    _setup_logging()
    config.require_startup_settings()
    _acquire_lock()
    try:
        scheduler = BlockingScheduler()
        scheduler.add_job(
            run_check,
            "interval",
            minutes=config.CHECK_INTERVAL_MINUTES,
            max_instances=1,  # прогон дольше интервала — не запускать параллельно
            coalesce=True,    # пропущенные запуски схлопывать в один
        )
        run_check()  # первая проверка сразу, не ждём интервал
        logging.getLogger(__name__).info(
            "Демон запущен, проверка каждые %d минут", config.CHECK_INTERVAL_MINUTES
        )
        scheduler.start()
    finally:
        _release_lock()


if __name__ == "__main__":
    main()
