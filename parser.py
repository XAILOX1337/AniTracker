import logging
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.sync_api import sync_playwright

log = logging.getLogger(__name__)

BASE_URL = "https://v5.animelib.org"


@dataclass
class Notification:
    """Контракт между parser, repository и notifier."""

    title_id: int | None  # числовой ID тайтла на AnimeLib (из URL)
    title_name: str
    team_name: str
    episode_number: int | None
    quality: str
    url: str
    raw_text: str


_TIME_RE = re.compile(r"\bназад\s*$", re.IGNORECASE)
_EPISODE_RE = re.compile(r"Эпизод\s+(\d+)", re.IGNORECASE)
_CHAPTER_RE = re.compile(r"Глава\s+(\d+)", re.IGNORECASE)
_DUB_RE = re.compile(r"Озвучка от\s+(.+?)(?:\s*\(плеер|$)", re.IGNORECASE)
_QUALITY_RE = re.compile(r"\b(4k|fullhd|full hd|hd|sd|1080p|720p|480p)\b", re.IGNORECASE)
_TITLE_PREFIX = "В тайтле"


def _extract_episode_number(lines: list[str]) -> int | None:
    for line in lines:
        match = _EPISODE_RE.search(line) or _CHAPTER_RE.search(line)
        if match:
            return int(match.group(1))
    return None


def _extract_title(lines: list[str]) -> str:
    for line in reversed(lines):
        if line.startswith(_TITLE_PREFIX):
            return line[len(_TITLE_PREFIX):].strip()
    return lines[-1] if lines else ""


def _extract_team(lines: list[str]) -> str:
    for line in lines:
        dub = _DUB_RE.search(line)
        if dub:
            return dub.group(1).strip()
    # Формат манги: команда — первая строка (если это не время и не строка про эпизод)
    first = lines[0] if lines else ""
    if first and not _TIME_RE.search(first) and not _EPISODE_RE.search(first) \
            and not first.startswith(_TITLE_PREFIX):
        return first
    return ""


# ID тайтла в пути ссылки: /ru/anime/25412--ao-no-hako-season-2-anime
_SITE_ID_RE = re.compile(r"/(\d+)--")


def _canonicalize_url(href: str | None) -> tuple[str, int | None]:
    """Абсолютный URL без query/fragment (сессионные параметры типа ?ui=)
    и числовой ID тайтла из пути ссылки."""
    if not href:
        return "", None
    parts = urlparse(urljoin(BASE_URL, href))
    url = urlunparse(parts._replace(query="", fragment=""))
    site_id = _SITE_ID_RE.search(parts.path)
    return url, int(site_id.group(1)) if site_id else None


def _extract_notification(div_text: str, href: str | None) -> Notification:
    lines = [line.strip() for line in div_text.splitlines() if line.strip()]
    quality = _QUALITY_RE.search(div_text)
    url, title_id = _canonicalize_url(href)
    return Notification(
        title_id=title_id,
        title_name=_extract_title(lines),
        team_name=_extract_team(lines),
        episode_number=_extract_episode_number(lines),
        quality=quality.group(1).lower() if quality else "",
        url=url,
        raw_text=div_text.strip(),
    )


def parse_notifications(url: str, user_data_dir: str) -> list[Notification]:
    """Открывает страницу уведомлений и возвращает список уведомлений."""
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(user_data_dir, headless=False)
        try:
            page = browser.new_page()
            page.goto(url)
            page.wait_for_selector("div.fade-2")
            notifications = []
            for locator in page.locator("div.fade-2").all():
                text = locator.inner_text().strip()
                href = locator.locator("a").first.get_attribute("href")
                if not text:
                    continue
                notifications.append(_extract_notification(text, href))
            log.info("Спарсено уведомлений: %d", len(notifications))
            return notifications
        finally:
            browser.close()
