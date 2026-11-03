import atexit
import ctypes
import logging
import os
import sys
import time

from apscheduler.schedulers.background import BackgroundScheduler

import config
import tracker

LOCK_FILE = "anitracker.lock"
LOG_FILE = "anitracker.log"

log = logging.getLogger(__name__)


def _pid_alive(pid: int) -> bool:
    """Проверка, жив ли процесс с данным PID (Windows-способ —
    os.kill(pid, 0) на Windows не подходит: он убивает процесс)."""
    handle = ctypes.windll.kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
    if not handle:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def _acquire_lock() -> None:
    """Защита от двух одновременно запущенных копий демона.

    В lock-файл пишем PID: если процесс с таким PID мёртв, lock считается
    устаревшим (демон убили) и удаляется без ручного вмешательства.
    """
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, encoding="ascii") as f:
                pid = int(f.read().strip())
        except (ValueError, OSError):
            pid = None
        if pid and _pid_alive(pid):
            sys.exit(f"Демон уже запущен (PID {pid})")
        log.warning("Найден устаревший anitracker.lock, удаляю")
        os.remove(LOCK_FILE)
    fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode("ascii"))
    os.close(fd)


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
    # httpx на INFO пишет полные URL запросов — в них токен бота
    logging.getLogger("httpx").setLevel(logging.WARNING)


def run_check() -> None:
    try:
        tracker.check_once(config.URL, config.USER_DATA_DIR)
    except Exception:
        log.exception("Проверка завершилась с ошибкой")


STOP_COMMANDS = {"stop", "q", "quit", "exit"}


def _command_loop(scheduler) -> None:
    """Чтение команд из консоли: stop/q/quit/exit останавливают демон.

    Работает в любом терминале, где Ctrl+C может не доходить
    (Git Bash mintty, VS Code), — демон сам читает stdin.
    """
    print("Команды: stop — остановить демон")
    try:
        while True:
            command = input().strip().lower()
            if command in STOP_COMMANDS:
                log.info("Остановка по команде из консоли")
                scheduler.shutdown(wait=False)
                return
            if command:
                print(f"Неизвестная команда: {command}")
    except (EOFError, KeyboardInterrupt):
        # EOF: stdin закрыт (запуск без консоли); Ctrl+C: штатное прерывание
        log.info("Остановлено")


def main() -> None:
    _setup_logging()
    config.require_startup_settings()
    _acquire_lock()
    atexit.register(_release_lock)  # lock снимается при любом штатном выходе
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_check,
        "interval",
        minutes=config.CHECK_INTERVAL_MINUTES,
        max_instances=1,  # прогон дольше интервала — не запускать параллельно
        coalesce=True,    # пропущенные запуски схлопывать в один
    )
    scheduler.start()
    run_check()  # первая проверка сразу, не ждём интервал
    log.info("Демон запущен (PID %d), проверка каждые %d минут",
             os.getpid(), config.CHECK_INTERVAL_MINUTES)
    if sys.stdin.isatty():
        _command_loop(scheduler)
    else:
        # Запуск без консоли (Task Scheduler): просто держим процесс живым
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            log.info("Остановлено по Ctrl+C")
        finally:
            scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
