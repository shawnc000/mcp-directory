"""README excerpt and search-text helpers. Quotes stay quotes."""

from __future__ import annotations

import html
import re

_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_HTML_TAG_LINE = re.compile(r"</?[A-Za-z][^>]*>")
_IMAGE_ONLY = re.compile(
    r"^(?:!\[[^\]]*\]\([^)]+\)\s*|\[[^\]]*\]\([^)]+\)\s*)+$"
)
_BADGE = re.compile(r"img\.shields\.io|badge\.svg|github\.com/.+/workflows/.+/badge", re.I)
_HEADING = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_MD_CODE = re.compile(r"`([^`]*)`")
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def excerpt_readme(markdown: str | None, limit: int = 1400) -> str | None:
    if not markdown:
        return None
    text = _COMMENT.sub("", markdown)
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if _BADGE.search(stripped) and ("![" in stripped or stripped.startswith("<img") or "badge" in stripped.lower()):
            continue
        if stripped.startswith("<img ") or stripped.startswith("<img>"):
            continue
        if _IMAGE_ONLY.fullmatch(stripped):
            continue
        if stripped.startswith("<") and _HTML_TAG_LINE.fullmatch(stripped) and "CAUTION" not in stripped:
            continue
        kept.append(line.rstrip())
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()
    if not cleaned:
        return None
    if len(cleaned) <= limit:
        return cleaned
    cut = cleaned[:limit]
    newline = cut.rfind("\n")
    if newline > int(limit * 0.55):
        cut = cut[:newline]
    return cut.rstrip() + "\n…"


def readme_title(markdown: str | None) -> str | None:
    if not markdown:
        return None
    text = _COMMENT.sub("", markdown)
    # Prefer an explicit h1 inside a div, then a markdown heading.
    html_h1 = re.search(r"<h1[^>]*>(.*?)</h1>", text, flags=re.IGNORECASE | re.DOTALL)
    if html_h1:
        title = _plain_inline(html_h1.group(1))
        if _good_title(title):
            return title
    for match in _HEADING.finditer(text):
        title = _plain_inline(match.group(1))
        if _good_title(title):
            return title
    return None


def _plain_inline(value: str) -> str:
    value = _MD_IMAGE.sub("", value)
    value = _MD_LINK.sub(r"\1", value)
    value = _MD_CODE.sub(r"\1", value)
    value = _TAG.sub("", value)
    value = value.replace("**", "").replace("__", "").replace("*", "")
    return _WS.sub(" ", value).strip(" -–—")


def _good_title(title: str) -> bool:
    if not title:
        return False
    lowered = title.lower()
    if lowered in {"readme", "readme.md", "table of contents", "overview"}:
        return False
    return 2 <= len(title) <= 80


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def mostly_chinese(text: str | None) -> bool:
    if not text:
        return False
    return len(re.findall(r"[\u4e00-\u9fff]", text)) >= 6


def search_text(*parts: object) -> str:
    blob = " ".join("" if part is None else str(part) for part in parts)
    blob = blob.replace("\n", " ").replace("\r", " ")
    return _WS.sub(" ", blob).strip().lower()
