import unittest

from directory.textutil import excerpt_readme, readme_title

SAMPLE = """<!-- logo -->
<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="license">
</p>
# Elasticsearch MCP Server
> [!CAUTION]
> This MCP server is deprecated and will only receive critical security updates going forward.

The server connects agents to an Elasticsearch cluster.
"""


class TextUtilTests(unittest.TestCase):
    def test_title_skips_badges_and_uses_heading(self):
        self.assertEqual(readme_title(SAMPLE), "Elasticsearch MCP Server")

    def test_excerpt_keeps_caution_and_drops_badge_image(self):
        excerpt = excerpt_readme(SAMPLE)
        self.assertIn("deprecated", excerpt)
        self.assertNotIn("img.shields.io", excerpt)

    def test_html_h1_preferred_when_present(self):
        text = "<h1>LiteLLM</h1>\n# Other"
        self.assertEqual(readme_title(text), "LiteLLM")

    def test_empty_readme(self):
        self.assertIsNone(excerpt_readme(None))
        self.assertIsNone(readme_title("   "))

    def test_excerpt_truncates_long_text(self):
        long = "# Title\n\n" + ("word " * 800)
        excerpt = excerpt_readme(long, limit=200)
        self.assertTrue(excerpt.endswith("…"))
        self.assertLess(len(excerpt), 250)


if __name__ == "__main__":
    unittest.main()
