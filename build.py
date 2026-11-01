#!/usr/bin/env python3
"""Fetch public GitHub metadata and write the static directory to ./site."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from directory.fetch import GitHubError, fetch_readme, fetch_repository
from directory.model import tool_from_api
from directory.render import Site, render_site
from directory.taxonomy import CATEGORIES, slugify

ROOT = Path(__file__).resolve().parent
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
LABEL_TO_ID = {category["en"]: category["id"] for category in CATEGORIES}
KNOWN = set(LABEL_TO_ID.values())


def load_catalog(path: Path) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    tools = document["tools"] if isinstance(document, dict) else document
    seen: set[str] = set()
    normalized = []
    for entry in tools:
        repo = entry["repo"]
        if not REPO_RE.fullmatch(repo):
            raise SystemExit(f"invalid repository name: {repo}")
        label = entry["category"]
        category_id = LABEL_TO_ID.get(label, label if label in KNOWN else None)
        if category_id is None:
            raise SystemExit(f"unknown category for {repo}: {label}")
        key = repo.lower()
        if key in seen:
            raise SystemExit(f"duplicate repository: {repo}")
        seen.add(key)
        item = dict(entry)
        item["category"] = category_id
        normalized.append(item)
    if len(normalized) < 50:
        raise SystemExit(f"catalog has {len(normalized)} repositories; need at least 50")
    return normalized


def load_translations(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in raw.items() if value}


def _snapshot_repo(entry: dict) -> dict:
    meta = entry["meta"]
    repo_name = entry["repo"]
    return {
        "full_name": repo_name,
        "description": entry.get("desc") or None,
        "stargazers_count": meta["stargazers_count"],
        "pushed_at": meta.get("pushed_at"),
        "license": meta.get("license") or {},
        "topics": meta.get("topics") or [],
        "html_url": f"https://github.com/{repo_name}",
    }


def fetch_one(entry: dict, cache: Path | None, fetched_at: datetime, translations: dict[str, str]):
    repo_name = entry["repo"]
    desc_snapshot = entry.get("desc") or ""
    desc_zh = translations.get(repo_name) or entry.get("desc_zh") or ""
    try:
        repo = fetch_repository(repo_name, cache)
        readme, readme_error = fetch_readme(repo["full_name"], cache)
        tool = tool_from_api(
            repo,
            entry["category"],
            fetched_at,
            readme,
            readme_error,
            desc_zh=desc_zh,
            desc_snapshot=desc_snapshot,
            catalog_name=entry.get("name"),
            data_source="github-api",
        )
        return tool, None
    except (KeyError, ValueError, TypeError) as error:
        return None, f"{repo_name}: {error}"
    except GitHubError as error:
        if not entry.get("meta"):
            return None, f"{repo_name}: {error.status} and no snapshot"
        try:
            tool = tool_from_api(
                _snapshot_repo(entry),
                entry["category"],
                fetched_at,
                None,
                f"HTTP {error.status}",
                desc_zh=desc_zh,
                desc_snapshot=desc_snapshot,
                catalog_name=entry.get("name"),
                data_source="catalog-snapshot",
            )
        except (KeyError, ValueError, TypeError) as snapshot_error:
            return None, f"{repo_name}: {snapshot_error}"
        print(f"{repo_name}: using catalog snapshot after HTTP {error.status}", file=sys.stderr)
        return tool, None


def main() -> int:
    if not os.environ.get("GITHUB_TOKEN", "").strip():
        print("GITHUB_TOKEN is required so the GitHub API rate limit can cover the catalog.", file=sys.stderr)
        return 2
    catalog = load_catalog(ROOT / "data" / "catalog.json")
    translations = load_translations(ROOT / "data" / "desc_zh.json")
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0)
    cache_value = os.environ.get("DIRECTORY_CACHE_DIR", "").strip()
    cache = Path(cache_value) if cache_value else None
    origin = os.environ.get("SITE_ORIGIN", "https://shawnc000.github.io").rstrip("/")
    base = os.environ.get("SITE_BASE", "/mcp-directory").rstrip("/")
    output = Path(os.environ.get("SITE_OUTPUT", ROOT / "site"))
    failures: list[str] = []
    tools = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch_one, entry, cache, fetched_at, translations) for entry in catalog]
        for future in as_completed(futures):
            tool, error = future.result()
            if error:
                failures.append(error)
                print(error, file=sys.stderr)
            else:
                tools.append(tool)
    if failures:
        print(f"{len(failures)} repositories failed; not publishing a partial catalog.", file=sys.stderr)
        return 1
    canonical: dict[str, object] = {}
    for tool in tools:
        key = tool.full_name.lower()
        if key in canonical:
            print(f"duplicate after redirect: {tool.full_name}", file=sys.stderr)
            return 1
        canonical[key] = tool
    tools.sort(key=lambda tool: (-tool.breakdown.total, -tool.stars, tool.full_name.lower()))
    if output.exists():
        shutil.rmtree(output)
    assets = ROOT / "directory"
    site = Site(origin=origin, base=base, fetched_at=fetched_at, tools=tools)
    render_site(site, output, assets, min_tools=50)
    live = sum(1 for tool in tools if tool.data_source == "github-api")
    print(f"{len(tools)} tools written to {output} at {site.fetched_stamp} ({live} live, {len(tools) - live} snapshot)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
