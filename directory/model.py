"""A directory entry assembled only from a GitHub API payload."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from directory.score import Breakdown, score_breakdown
from directory.textutil import excerpt_readme, readme_title, search_text


@dataclass(frozen=True)
class Tool:
    full_name: str
    description: str | None
    homepage: str | None
    stars: int
    forks: int | None
    open_issues: int | None
    watchers: int | None
    language: str | None
    topics: tuple[str, ...]
    license_spdx: str | None
    license_name: str | None
    pushed_at: str | None
    updated_at: str | None
    created_at: str | None
    archived: bool | None
    default_branch: str
    category: str
    readme_title: str | None
    readme_excerpt: str | None
    readme_error: str | None
    html_url: str
    breakdown: Breakdown
    desc_zh: str | None = None
    desc_snapshot: str | None = None
    catalog_name: str | None = None
    catalog_repo: str | None = None
    data_source: str = "github-api"
    source_url: str | None = None
    last_verified_date: str | None = None

    @property
    def slug(self) -> str:
        owner, name = self.full_name.split("/", 1)
        return f"{owner}--{name}".lower()

    def search_blob(self, category_en: str, category_zh: str) -> str:
        return search_text(
            self.full_name,
            self.readme_title,
            self.description,
            self.language,
            self.license_spdx,
            self.license_name,
            self.category,
            category_en,
            category_zh,
            self.desc_zh,
            " ".join(self.topics),
        )


def _http_homepage(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    if any(ch.isspace() for ch in value):
        return None
    if value.startswith("https://") or value.startswith("http://"):
        return value
    return None


_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _verified_pair(source_url: str | None, last_verified_date: str | None) -> tuple[str | None, str | None]:
    """Keep the pair only when both values came from a real confirmation."""
    if not source_url or not last_verified_date:
        return None, None
    if not source_url.startswith("https://github.com/") or any(ch.isspace() for ch in source_url):
        return None, None
    if not _DATE.fullmatch(last_verified_date):
        return None, None
    return source_url, last_verified_date


def translation_applies(live: str | None, snapshot: str | None, translated: str | None) -> str | None:
    """Keep a Chinese translation only while it still matches the GitHub description."""
    if not translated or not snapshot or not live:
        return None
    live_text = live.strip()
    snap = snapshot.strip()
    if not snap:
        return None
    if live_text == snap or live_text.startswith(snap):
        return translated.strip()
    return None


def tool_from_api(
    repo: dict,
    category: str,
    fetched_at: datetime,
    readme: str | None = None,
    readme_error: str | None = None,
    desc_zh: str | None = None,
    desc_snapshot: str | None = None,
    catalog_name: str | None = None,
    catalog_repo: str | None = None,
    data_source: str = "github-api",
    source_url: str | None = None,
    last_verified_date: str | None = None,
) -> Tool:
    full_name = repo["full_name"]
    if full_name.count("/") != 1:
        raise ValueError(f"unexpected full_name: {full_name}")
    license_obj = repo.get("license") or {}
    spdx = license_obj.get("spdx_id") or None
    description = repo.get("description")
    if isinstance(description, str):
        description = description.strip() or None
    else:
        description = None
    stars = int(repo.get("stargazers_count") or 0)
    pushed_at = repo.get("pushed_at")

    def optional_int(key: str) -> int | None:
        if key not in repo or repo.get(key) is None:
            return None
        return int(repo[key])
    raw_html = repo.get("html_url")
    if isinstance(raw_html, str) and raw_html.startswith("https://github.com/") and not any(ch.isspace() for ch in raw_html):
        html_url = raw_html
    else:
        html_url = f"https://github.com/{full_name}"
    if data_source == "github-api":
        source_url, last_verified_date = _verified_pair(source_url, last_verified_date)
    else:
        source_url, last_verified_date = None, None
    topics = tuple(str(topic) for topic in (repo.get("topics") or []))
    return Tool(
        full_name=full_name,
        description=description,
        homepage=_http_homepage(repo.get("homepage")),
        stars=stars,
        forks=optional_int("forks_count"),
        open_issues=optional_int("open_issues_count"),
        watchers=optional_int("subscribers_count"),
        language=repo.get("language") or None,
        topics=topics,
        license_spdx=spdx,
        license_name=(license_obj.get("name") or None),
        pushed_at=pushed_at,
        updated_at=repo.get("updated_at"),
        created_at=repo.get("created_at"),
        archived=bool(repo["archived"]) if "archived" in repo else None,
        default_branch=repo.get("default_branch") or "HEAD",
        category=category,
        readme_title=readme_title(readme),
        readme_excerpt=excerpt_readme(readme),
        readme_error=readme_error,
        html_url=html_url,
        breakdown=score_breakdown(stars, pushed_at, spdx, fetched_at),
        desc_zh=translation_applies(description, desc_snapshot, desc_zh),
        desc_snapshot=desc_snapshot,
        catalog_name=catalog_name,
        catalog_repo=catalog_repo,
        data_source=data_source,
        source_url=source_url,
        last_verified_date=last_verified_date,
    )
