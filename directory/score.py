"""Public-signal score.

The score uses three numbers GitHub publishes for a repository: star count,
the ``pushed_at`` timestamp, and the SPDX license id. It is formula version 1.

Star points cap at 50, so repositories with roughly 316 stars or more tie on
that component. Activity and license still separate them, and the raw star
count is always shown beside the score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

FORMULA_VERSION = "1"
STAR_CAP = 50
STAR_LOG_COEFFICIENT = 20
ACTIVITY_RECENT_DAYS = 30
ACTIVITY_RECENT_POINTS = 30
ACTIVITY_MID_DAYS = 180
ACTIVITY_MID_POINTS = 15
LICENSE_POINTS = 20

# stars + 1 >= 10 ** (STAR_CAP / STAR_LOG_COEFFICIENT)
STAR_CAP_THRESHOLD = 10 ** (STAR_CAP / STAR_LOG_COEFFICIENT)


@dataclass(frozen=True)
class Breakdown:
    stars: int
    star_raw: float
    star_points: float
    pushed_at: str | None
    days_since_push: int | None
    push_parse_error: bool
    activity_points: int
    license_spdx: str | None
    license_points: int
    total: int
    fetched_at: str

    def sum_before_round(self) -> float:
        return self.star_points + self.activity_points + self.license_points


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_pushed(pushed_at: str | None) -> tuple[datetime | None, bool]:
    if pushed_at is None or pushed_at == "":
        return None, False
    try:
        parsed = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None, True
    return parsed, False


def activity_points_for_days(days: int | None, parse_error: bool) -> int:
    if parse_error or days is None:
        return 0
    # A future push timestamp is clock skew. Treat it as recent and say so.
    if days < ACTIVITY_RECENT_DAYS:
        return ACTIVITY_RECENT_POINTS
    if days < ACTIVITY_MID_DAYS:
        return ACTIVITY_MID_POINTS
    return 0


def score_breakdown(
    stars: int,
    pushed_at: str | None,
    spdx_id: str | None,
    fetched_at: datetime,
) -> Breakdown:
    if stars < 0:
        raise ValueError("stars must be >= 0")
    fetched = _as_utc(fetched_at)
    raw = STAR_LOG_COEFFICIENT * math.log10(stars + 1)
    capped = min(float(STAR_CAP), raw)
    pushed_dt, parse_error = _parse_pushed(pushed_at)
    days: int | None
    if pushed_dt is None:
        days = None
    else:
        days = (fetched - pushed_dt).days
    activity = activity_points_for_days(days, parse_error)
    spdx = spdx_id if spdx_id else None
    license_points = LICENSE_POINTS if spdx not in (None, "NOASSERTION") else 0
    total = round(capped + activity + license_points)
    return Breakdown(
        stars=stars,
        star_raw=raw,
        star_points=capped,
        pushed_at=pushed_at if pushed_at else None,
        days_since_push=days,
        push_parse_error=parse_error,
        activity_points=activity,
        license_spdx=spdx,
        license_points=license_points,
        total=total,
        fetched_at=fetched.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
