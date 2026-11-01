import unittest
from datetime import datetime, timezone
from pathlib import Path
import tempfile

from directory.model import tool_from_api
from directory.render import Site, render_site

FETCHED = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
ASSETS = Path(__file__).resolve().parents[1] / "directory"


def sample_tool():
    repo = {
        "full_name": "example/demo-mcp",
        "description": 'A <script>alert(1)</script> server',
        "stargazers_count": 100,
        "forks_count": 3,
        "open_issues_count": 2,
        "subscribers_count": 4,
        "language": "Python",
        "topics": ["mcp"],
        "license": {"spdx_id": "MIT", "name": "MIT License"},
        "pushed_at": "2026-10-20T00:00:00Z",
        "updated_at": "2026-10-21T00:00:00Z",
        "created_at": "2024-01-01T00:00:00Z",
        "homepage": "javascript:alert(1)",
        "archived": False,
        "default_branch": "main",
        "html_url": "https://github.com/example/demo-mcp",
    }
    readme = "# Demo MCP\n\nReads pages.\n"
    return tool_from_api(repo, "browser", FETCHED, readme, None)


class RenderTests(unittest.TestCase):
    def test_bilingual_pages_escape_html_and_explain_score(self):
        tool = sample_tool()
        self.assertIsNone(tool.homepage)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = Site("https://shawnc000.github.io", "/mcp-directory", FETCHED, [tool])
            render_site(site, root, ASSETS, min_tools=1)
            zh = (root / "tools" / "example--demo-mcp" / "index.html").read_text(encoding="utf-8")
            page = (root / "en" / "tools" / "example--demo-mcp" / "index.html").read_text(encoding="utf-8")
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
            self.assertNotIn("<script>alert", page)
            self.assertIn("log10(100 + 1)", page)
            self.assertIn("Security assessment", page)
            self.assertIn("2026-11-01T12:00:00Z", page)
            self.assertIn(str(tool.breakdown.total), page)
            self.assertIn("公开安全评估", zh)
            self.assertIn("星标分", zh)
            self.assertIn("log10(100 + 1)", zh)
            self.assertIn('hreflang="zh-Hans"', zh)
            self.assertIn('hreflang="x-default" href="https://shawnc000.github.io/mcp-directory/tools/example--demo-mcp/"', zh)
            featured = (root / "en" / "featured" / "index.html").read_text(encoding="utf-8")
            zh_featured = (root / "featured" / "index.html").read_text(encoding="utf-8")
            self.assertIn("Coming soon", featured)
            self.assertIn("即将推出", zh_featured)
            self.assertNotIn("$49", zh_featured)
            self.assertNotIn("gumroad", zh_featured.lower())
            robots = (root / "robots.txt").read_text(encoding="utf-8")
            self.assertIn("https://shawnc000.github.io/mcp-directory/sitemap.xml", robots)
            sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("https://shawnc000.github.io/mcp-directory/tools/example--demo-mcp/", sitemap)
            self.assertIn("https://shawnc000.github.io/mcp-directory/en/tools/example--demo-mcp/", sitemap)
            self.assertIn("https://github.com/shawnc000/mcp-directory/issues/new?template=submit-tool.yml", (root / "submit" / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
