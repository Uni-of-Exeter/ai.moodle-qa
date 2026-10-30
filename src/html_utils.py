"""
src/html_utils.py — Shared HTML parsing helpers.

Keeps BeautifulSoup usage in one place so checks stay focused on logic.
"""

import re
from bs4 import BeautifulSoup, Tag


def parse(html: str) -> BeautifulSoup:
    """Parse an HTML string and return a BeautifulSoup tree."""
    return BeautifulSoup(html, "html.parser")


def extract_urls(html: str) -> set[str]:
    """Return all absolute URLs found in href / src attributes."""
    soup = parse(html)
    urls: set[str] = set()
    for tag in soup.find_all(["a", "img", "video", "audio", "source", "iframe", "embed"]):
        url = tag.get("href") or tag.get("src")
        if url and url.startswith(("http://", "https://")):
            urls.add(url)
    return urls


def find_images_without_alt(soup: BeautifulSoup) -> list[Tag]:
    return [img for img in soup.find_all("img") if not img.get("alt", "").strip()]


def find_empty_links(soup: BeautifulSoup) -> list[Tag]:
    return [a for a in soup.find_all("a") if not a.get_text(strip=True) and not a.find("img")]


def find_tables_without_headers(soup: BeautifulSoup) -> list[Tag]:
    return [t for t in soup.find_all("table") if not t.find("th")]


def find_heading_skips(soup: BeautifulSoup) -> list[tuple[int, int]]:
    """Return pairs (prev_level, curr_level) where a heading level was skipped."""
    headings = soup.find_all(re.compile(r"^h[1-6]$"))
    skips = []
    for i in range(1, len(headings)):
        prev = int(headings[i - 1].name[1])
        curr = int(headings[i].name[1])
        if curr > prev + 1:
            skips.append((prev, curr))
    return skips


def has_fixed_pixel_width(soup: BeautifulSoup) -> bool:
    for tag in soup.find_all(style=True):
        if re.search(r"width\s*:\s*\d{3,}px", tag.get("style", "")):
            return True
    return False


def has_flash_embed(soup: BeautifulSoup) -> bool:
    for embed in soup.find_all(["embed", "object"]):
        if "flash" in embed.get("type", "").lower() or "swf" in str(embed).lower():
            return True
    return False
