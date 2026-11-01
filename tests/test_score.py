import math
import unittest
from datetime import datetime, timedelta, timezone

from directory.explain import activity_sentence
from directory.score import (
    STAR_CAP,
    STAR_LOG_COEFFICIENT,
    score_breakdown,
)

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def pushed_days_before(days: int) -> str:
    return (NOW - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


class ScoreTests(unittest.TestCase):
    def test_zero_inputs_score_zero(self):
        breakdown = score_breakdown(0, None, None, NOW)
        self.assertEqual(breakdown.star_points, 0)
        self.assertEqual(breakdown.activity_points, 0)
        self.assertEqual(breakdown.license_points, 0)
        self.assertEqual(breakdown.total, 0)
        self.assertIsNone(breakdown.days_since_push)
        self.assertEqual(breakdown.fetched_at, "2026-11-01T12:00:00Z")

    def test_star_component_matches_published_formula(self):
        # 20 * log10(101) for 100 stars. Not capped.
        breakdown = score_breakdown(100, None, None, NOW)
        expected = STAR_LOG_COEFFICIENT * math.log10(101)
        self.assertAlmostEqual(breakdown.star_raw, expected, places=9)
        self.assertAlmostEqual(breakdown.star_points, expected, places=9)
        self.assertLess(breakdown.star_points, STAR_CAP)

    def test_star_cap_at_999_stars(self):
        # 20 * log10(1000) == 60, then capped at 50.
        breakdown = score_breakdown(999, None, None, NOW)
        self.assertAlmostEqual(breakdown.star_raw, 60.0, places=9)
        self.assertEqual(breakdown.star_points, 50.0)
        self.assertEqual(breakdown.total, 50)

    def test_activity_day_boundaries(self):
        self.assertEqual(score_breakdown(0, pushed_days_before(0), None, NOW).activity_points, 30)
        self.assertEqual(score_breakdown(0, pushed_days_before(29), None, NOW).activity_points, 30)
        self.assertEqual(score_breakdown(0, pushed_days_before(30), None, NOW).activity_points, 15)
        self.assertEqual(score_breakdown(0, pushed_days_before(179), None, NOW).activity_points, 15)
        self.assertEqual(score_breakdown(0, pushed_days_before(180), None, NOW).activity_points, 0)
        self.assertEqual(score_breakdown(0, pushed_days_before(400), None, NOW).activity_points, 0)

    def test_future_push_is_recent_but_visible(self):
        future = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        breakdown = score_breakdown(0, future, None, NOW)
        self.assertLess(breakdown.days_since_push, 0)
        self.assertEqual(breakdown.activity_points, 30)

    def test_unparsed_push_scores_no_activity(self):
        breakdown = score_breakdown(0, "yesterday", None, NOW)
        self.assertTrue(breakdown.push_parse_error)
        self.assertEqual(breakdown.activity_points, 0)
        self.assertIsNone(breakdown.days_since_push)

    def test_license_points(self):
        self.assertEqual(score_breakdown(0, None, "MIT", NOW).license_points, 20)
        self.assertEqual(score_breakdown(0, None, "Apache-2.0", NOW).license_points, 20)
        self.assertEqual(score_breakdown(0, None, "NOASSERTION", NOW).license_points, 0)
        self.assertEqual(score_breakdown(0, None, None, NOW).license_points, 0)
        self.assertEqual(score_breakdown(0, None, "", NOW).license_points, 0)

    def test_total_rounds_the_sum(self):
        breakdown = score_breakdown(100, pushed_days_before(10), "MIT", NOW)
        self.assertEqual(breakdown.activity_points, 30)
        self.assertEqual(breakdown.license_points, 20)
        self.assertEqual(breakdown.total, round(breakdown.sum_before_round()))
        self.assertGreater(breakdown.total, 80)

    def test_one_day_uses_singular(self):
        breakdown = score_breakdown(0, pushed_days_before(1), None, NOW)
        text = activity_sentence(breakdown, "en")
        self.assertIn("1 day since the push", text)
        self.assertNotIn("1 days", text)

    def test_negative_stars_rejected(self):
        with self.assertRaises(ValueError):
            score_breakdown(-1, None, None, NOW)


if __name__ == "__main__":
    unittest.main()
