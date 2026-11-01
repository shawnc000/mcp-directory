"""Sentences that show the arithmetic for one repository."""

from __future__ import annotations

from directory.score import (
    ACTIVITY_MID_DAYS,
    ACTIVITY_MID_POINTS,
    ACTIVITY_RECENT_DAYS,
    ACTIVITY_RECENT_POINTS,
    FORMULA_VERSION,
    LICENSE_POINTS,
    STAR_CAP,
    STAR_CAP_THRESHOLD,
    Breakdown,
)


def star_sentence(b: Breakdown, lang: str) -> str:
    raw = f"{b.star_raw:.2f}"
    points = f"{b.star_points:.2f}"
    threshold = f"{STAR_CAP_THRESHOLD:.2f}"
    if lang == "zh":
        return (
            f"星标分 = min({STAR_CAP}, 20 × log10({b.stars} + 1)) = min({STAR_CAP}, {raw}) = {points}。"
            f"当 stars + 1 达到 10^({STAR_CAP}/20) ≈ {threshold}（大约 {int(STAR_CAP_THRESHOLD)} 个 star）时，这一项触及 {STAR_CAP} 分上限。"
            f"超过上限后，更多 star 不再提高分数，页面仍会列出原始 star 数。"
        )
    return (
        f"Star points = min({STAR_CAP}, 20 × log10({b.stars} + 1)) = min({STAR_CAP}, {raw}) = {points}. "
        f"This component reaches the cap of {STAR_CAP} when stars + 1 is at least 10^({STAR_CAP}/20) ≈ {threshold} "
        f"(about {int(STAR_CAP_THRESHOLD)} stars). Past the cap, more stars do not raise the score. The raw star count is still shown."
    )


def activity_sentence(b: Breakdown, lang: str) -> str:
    rules_en = (
        f"Under {ACTIVITY_RECENT_DAYS} days scores {ACTIVITY_RECENT_POINTS}; "
        f"at least {ACTIVITY_RECENT_DAYS} and under {ACTIVITY_MID_DAYS} scores {ACTIVITY_MID_POINTS}; "
        f"{ACTIVITY_MID_DAYS} or more scores 0."
    )
    rules_zh = (
        f"小于 {ACTIVITY_RECENT_DAYS} 天得 {ACTIVITY_RECENT_POINTS} 分；"
        f"满 {ACTIVITY_RECENT_DAYS} 天且小于 {ACTIVITY_MID_DAYS} 天得 {ACTIVITY_MID_POINTS} 分；"
        f"满 {ACTIVITY_MID_DAYS} 天得 0 分。"
    )
    if b.push_parse_error:
        if lang == "zh":
            return f"活跃分 = 0。pushed_at 的值「{b.pushed_at}」无法按 UTC 时间 YYYY-MM-DDTHH:MM:SSZ 解析。{rules_zh}"
        return (
            f"Activity points = 0 because pushed_at ({b.pushed_at}) is not a UTC timestamp in the form YYYY-MM-DDTHH:MM:SSZ. {rules_en}"
        )
    if b.days_since_push is None:
        if lang == "zh":
            return f"活跃分 = 0。GitHub API 没有返回 pushed_at。{rules_zh}"
        return f"Activity points = 0 because the GitHub API did not return pushed_at. {rules_en}"
    days = b.days_since_push
    unit = "day" if abs(days) == 1 else "days"
    if lang == "zh":
        if days < 0:
            band = f"该时间比本次抓取超前 {abs(days)} 天，按时钟偏差处理，落入「小于 {ACTIVITY_RECENT_DAYS} 天」一档。"
        elif days < ACTIVITY_RECENT_DAYS:
            band = f"间隔 {days} 天，小于 {ACTIVITY_RECENT_DAYS}，落入最近一档。"
        elif days < ACTIVITY_MID_DAYS:
            band = f"间隔 {days} 天，已满 {ACTIVITY_RECENT_DAYS} 且小于 {ACTIVITY_MID_DAYS}，落入中间一档。"
        else:
            band = f"间隔 {days} 天，已满 {ACTIVITY_MID_DAYS}，落入最旧一档。"
        return (
            f"活跃分 = {b.activity_points}。天数是 pushed_at（{b.pushed_at}）到本次抓取之间的完整 UTC 天数。{band}{rules_zh}"
            "评分用的是 pushed_at（代码推送），不是 updated_at（议题或维基也会改这个时间）。"
        )
    if days < 0:
        band = (
            f"That timestamp is {abs(days)} {unit} ahead of the fetch clock, so it is treated as clock skew "
            f"and uses the under-{ACTIVITY_RECENT_DAYS}-day band."
        )
    elif days < ACTIVITY_RECENT_DAYS:
        band = f"{days} {unit} since the push is under {ACTIVITY_RECENT_DAYS}, so the recent band applies."
    elif days < ACTIVITY_MID_DAYS:
        band = (
            f"{days} {unit} since the push is at least {ACTIVITY_RECENT_DAYS} and under {ACTIVITY_MID_DAYS}, so the middle band applies."
        )
    else:
        band = f"{days} {unit} since the push is {ACTIVITY_MID_DAYS} or more, so the oldest band applies."
    return (
        f"Activity points = {b.activity_points}. Days are whole UTC days from pushed_at ({b.pushed_at}) to this fetch. "
        f"{band} {rules_en} The input is pushed_at (a git push), not updated_at, which also moves when issues or the wiki change."
    )


def license_sentence(b: Breakdown, lang: str) -> str:
    if b.license_spdx is None:
        if lang == "zh":
            return (
                "许可证分 = 0。GitHub API 没有返回 license 对象，spdx_id 为空。"
                "这和 NOASSERTION 不同：NOASSERTION 表示 GitHub 看到了许可证信息，但没有映射到 SPDX 标识。"
                "两种情况都是 0 分。"
            )
        return (
            "License points = 0 because the GitHub API returned no license object, so spdx_id is empty. "
            "That is different from NOASSERTION, which means GitHub saw license information it did not map to an SPDX id. "
            "Both cases score 0."
        )
    if b.license_spdx == "NOASSERTION":
        if lang == "zh":
            return (
                "许可证分 = 0，因为 spdx_id 是 NOASSERTION。"
                "GitHub 发现了它不愿意映射为 SPDX 标识的许可证信息。这不是「该项目没有许可条款」的判断。"
            )
        return (
            "License points = 0 because spdx_id is NOASSERTION. "
            "GitHub found license information it would not map to an SPDX id. "
            "This is not a finding that the project has no license terms."
        )
    if lang == "zh":
        return (
            f"许可证分 = {LICENSE_POINTS}，因为 spdx_id 是 {b.license_spdx}，有值，且不是 NOASSERTION。"
            "这一项只检查标识是否被识别，不判断条款是否适合你的用途。"
        )
    return (
        f"License points = {LICENSE_POINTS} because spdx_id is {b.license_spdx}, which is present and is not NOASSERTION. "
        "The points only mean GitHub identified an SPDX id. They do not say the terms fit your use."
    )


def total_sentence(b: Breakdown, lang: str) -> str:
    before = f"{b.sum_before_round():.2f}"
    if lang == "zh":
        return (
            f"总分 = round({b.star_points:.2f} + {b.activity_points} + {b.license_points}) = round({before}) = {b.total}。"
            f"舍入使用 Python 3 的 round（正好 .5 时向偶数舍入）。公式版本 {FORMULA_VERSION}。"
            f"数据抓取时间 {b.fetched_at}。"
        )
    return (
        f"Total = round({b.star_points:.2f} + {b.activity_points} + {b.license_points}) = round({before}) = {b.total}. "
        f"Rounding uses Python 3 round, which breaks exact halves toward even. Formula version {FORMULA_VERSION}. "
        f"Data fetched {b.fetched_at}."
    )
