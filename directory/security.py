"""Public security assessment.

The assessment repeats license, push age, archive state, and a few strings
that appear in the README excerpt. It does not assign a safety score.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from directory.score import Breakdown

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("deprecated", re.compile(r"deprecated|弃用|已废弃", re.IGNORECASE)),
    ("caution", re.compile(r"\[!CAUTION\]|\[!WARNING\]")),
    ("cve", re.compile(r"\bCVE-\d{4}-\d+\b", re.IGNORECASE)),
)


@dataclass(frozen=True)
class Assessment:
    license_spdx: str | None
    days_since_push: int | None
    push_known: bool
    archived: bool | None
    hits: tuple[str, ...]
    data_source: str


def readme_hits(excerpt: str | None) -> tuple[str, ...]:
    if not excerpt:
        return ()
    found = [name for name, pattern in _PATTERNS if pattern.search(excerpt)]
    return tuple(found)


def assess(breakdown: Breakdown, archived: bool | None, excerpt: str | None, data_source: str) -> Assessment:
    return Assessment(
        license_spdx=breakdown.license_spdx,
        days_since_push=breakdown.days_since_push,
        push_known=not breakdown.push_parse_error and breakdown.days_since_push is not None,
        archived=archived,
        hits=readme_hits(excerpt),
        data_source=data_source,
    )


def _maintenance_zh(days: int | None, known: bool) -> str:
    if not known or days is None:
        return "维护：未知。这次没有可用的 pushed_at，不能写成最近有人维护。"
    if days < 0:
        return f"维护：pushed_at 比本次抓取超前 {abs(days)} 天。按时钟偏差记入 30 天以内，不是「未来版本已审计」。"
    if days < 30:
        return f"维护：最近一次推送在 {days} 天前，小于 30 天。这只说明默认分支有推送，不说明这次推送修过安全问题。"
    if days < 180:
        return f"维护：最近一次推送在 {days} 天前，已满 30 天、未满 180 天。"
    return f"维护：最近一次推送在 {days} 天前，已满 180 天。星标再高也不改变这个间隔。"


def _maintenance_en(days: int | None, known: bool) -> str:
    if not known or days is None:
        return "Maintenance: unknown. This fetch has no usable pushed_at, so it is not described as recently maintained."
    if days < 0:
        return (
            f"Maintenance: pushed_at is {abs(days)} days ahead of this fetch. "
            "Clock skew is recorded in the under-30-day band. That is not an audit of a future release."
        )
    if days < 30:
        return (
            f"Maintenance: the latest push was {days} days ago, under 30. "
            "That means the default branch moved. It does not mean the push fixed a security issue."
        )
    if days < 180:
        return f"Maintenance: the latest push was {days} days ago, at least 30 and under 180."
    return (
        f"Maintenance: the latest push was {days} days ago, 180 or more. "
        "A high star count does not change that interval."
    )


def assessment_lines(item: Assessment, lang: str) -> list[str]:
    if item.license_spdx and item.license_spdx != "NOASSERTION":
        license_zh = f"许可证：GitHub 给出的 SPDX 标识是 {item.license_spdx}。这表示标识被识别，不表示条款适合你的产品。"
        license_en = (
            f"License: GitHub reports the SPDX id {item.license_spdx}. "
            "The id is identified. That is not a statement that the terms fit your product."
        )
    elif item.license_spdx == "NOASSERTION":
        license_zh = "许可证：spdx_id 是 NOASSERTION。GitHub 没有把它映射成 SPDX 标识。不要把它写成「没有许可条款」。"
        license_en = "License: spdx_id is NOASSERTION. GitHub did not map it to an SPDX id. Do not read that as 'no license terms exist'."
    else:
        license_zh = "许可证：这次没有 SPDX 标识。收录名单要求搜索时有许可证；若实时 API 不再返回，以这一行为准。"
        license_en = "License: this fetch has no SPDX id. The catalog required one at search time; if the live API no longer returns it, this line is the current fact."
    if item.archived is True:
        archive_zh = "归档：GitHub 标记为已归档。归档不是漏洞编号，它说明仓库不再按常规接收更新。"
        archive_en = "Archive: GitHub marks this repository archived. That is not a CVE. It means the repository is not taking normal updates."
    elif item.archived is False:
        archive_zh = "归档：GitHub 标记为未归档。未归档不等于有人在做安全维护。"
        archive_en = "Archive: GitHub marks this repository as not archived. Not archived does not mean someone is doing security maintenance."
    else:
        archive_zh = "归档：这次的数据里没有 archived 字段，不能写成未归档。"
        archive_en = "Archive: this payload has no archived field, so it is not described as unarchived."
    if item.hits:
        shown = ", ".join(item.hits)
        hit_zh = f"README 词面：摘录里匹配到 {shown}。这只表示原文出现了弃用说法、GitHub 警告块或 CVE 编号。打开下面的摘录核对原句，不要把它换成漏洞评分。"
        hit_en = (
            f"README wording: the excerpt matched {shown}. "
            "That means the quoted text contains a deprecation phrase, a GitHub alert, or a CVE id. "
            "Read the excerpt below. It is not a vulnerability score."
        )
    else:
        hit_zh = "README 词面：摘录里没有匹配到弃用说法、[!CAUTION]/[!WARNING] 或 CVE 编号。没有命中不等于安全。"
        hit_en = "README wording: the excerpt matched no deprecation phrase, [!CAUTION]/[!WARNING], or CVE id. No match is not a safety finding."
    source_zh = "数据来源：实时 GitHub 仓库 API。" if item.data_source == "github-api" else "数据来源：data/catalog.json 里保存的 GitHub 搜索快照，因为这次没能刷新这个仓库。"
    source_en = (
        "Source: the live GitHub repository API."
        if item.data_source == "github-api"
        else "Source: the GitHub search snapshot stored in data/catalog.json, because this repository could not be refreshed."
    )
    if lang == "zh":
        return [license_zh, _maintenance_zh(item.days_since_push, item.push_known), archive_zh, hit_zh, source_zh]
    return [license_en, _maintenance_en(item.days_since_push, item.push_known), archive_en, hit_en, source_en]
