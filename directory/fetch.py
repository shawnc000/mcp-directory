"""Fetch public GitHub repository metadata. No other data source."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "mcp-directory (https://github.com/shawnc000/mcp-directory)"
API = "https://api.github.com"


class GitHubError(RuntimeError):
    def __init__(self, repo: str, status: int | None, detail: str):
        super().__init__(f"{repo}: HTTP {status} {detail}")
        self.repo = repo
        self.status = status


def _token() -> str:
    return os.environ.get("GITHUB_TOKEN", "").strip()


def _request(url: str, accept: str) -> tuple[int, bytes]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = _token()
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            return response.status, response.read(120_000)
    except urllib.error.HTTPError as error:
        body = error.read(400).decode("utf-8", "replace")
        raise GitHubError(url, error.code, body[:180]) from None


def _request_retry(url: str, accept: str) -> tuple[int, bytes]:
    last: Exception | None = None
    for attempt in range(4):
        try:
            return _request(url, accept)
        except GitHubError as error:
            last = error
            if error.status in (403, 429, 500, 502, 503) and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise
    raise last  # pragma: no cover


def _cache_path(cache_dir: Path | None, full_name: str, kind: str) -> Path | None:
    if cache_dir is None:
        return None
    safe = full_name.replace("/", "__")
    return cache_dir / f"{safe}.{kind}.json"


def fetch_repository(full_name: str, cache_dir: Path | None = None) -> dict:
    path = _cache_path(cache_dir, full_name, "repo")
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    status, payload = _request_retry(
        f"{API}/repos/{full_name}",
        "application/vnd.github+json",
    )
    if status != 200:
        raise GitHubError(full_name, status, "unexpected status")
    data = json.loads(payload.decode("utf-8"))
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
    return data


def fetch_readme(full_name: str, cache_dir: Path | None = None) -> tuple[str | None, str | None]:
    """Return (markdown, error). A missing README is not fatal."""
    path = _cache_path(cache_dir, full_name, "readme")
    if path and path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        return cached.get("text"), cached.get("error")
    try:
        _status, payload = _request_retry(
            f"{API}/repos/{full_name}/readme",
            "application/vnd.github.raw",
        )
        text = payload.decode("utf-8", "replace")
        error = None
    except GitHubError as error:
        if error.status == 404:
            text, error_text = None, "HTTP 404"
        else:
            text, error_text = None, f"HTTP {error.status}"
        error = error_text
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"text": text, "error": error}), encoding="utf-8")
    return text, error
