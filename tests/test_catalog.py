import json
import unittest
from pathlib import Path

from directory.copy import CATEGORIES

ROOT = Path(__file__).resolve().parents[1]
KNOWN = {category["id"] for category in CATEGORIES}


class CatalogTests(unittest.TestCase):
    def test_catalog_has_the_v2_repos(self):
        from directory.taxonomy import slugify

        document = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
        self.assertIsInstance(document, list)
        self.assertGreaterEqual(len(document), 440)
        seen = set()
        labels = {category["en"] for category in CATEGORIES}
        licensed = 0
        for entry in document:
            repo = entry["repo"]
            self.assertRegex(repo, r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
            self.assertIn(entry["category"], labels)
            self.assertNotIn(repo.lower(), seen)
            seen.add(repo.lower())
            self.assertTrue(entry.get("desc") is not None)
            meta = entry.get("meta")
            if meta:
                self.assertIsInstance(meta["stargazers_count"], int)
                self.assertNotEqual(meta["license"].get("spdx_id"), "NOASSERTION")
                licensed += 1
            self.assertEqual(slugify(entry["category"]), slugify(entry["category"]))
        self.assertGreaterEqual(licensed, 430)


if __name__ == "__main__":
    unittest.main()
