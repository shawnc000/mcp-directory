import unittest

from directory.security import assess, readme_hits
from directory.score import score_breakdown
from datetime import datetime, timezone

NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)


class SecurityTests(unittest.TestCase):
    def test_hits_are_only_explicit_phrases(self):
        text = "Set your API token in the environment.\n> [!WARNING]\nThis server is deprecated.\nSee CVE-2024-12345."
        self.assertEqual(readme_hits(text), ("deprecated", "caution", "cve"))

    def test_token_alone_is_not_a_finding(self):
        self.assertEqual(readme_hits("Pass a token to the server."), ())

    def test_assessment_does_not_invent_archive_state(self):
        breakdown = score_breakdown(10, None, "MIT", NOW)
        item = assess(breakdown, None, None, "catalog-snapshot")
        lines = __import__("directory.security", fromlist=["assessment_lines"]).assessment_lines(item, "zh")
        self.assertTrue(any("不能写成未归档" in line for line in lines))
        self.assertTrue(any("没有可用的 pushed_at" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
