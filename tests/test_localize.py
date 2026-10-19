import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from localize import localize, relative_url


PAGE = '''<!doctype html><html lang="en"><head><meta charset="utf-8"></head><body>
<header id="quarto-header"><nav>
<a class="navbar-brand" href="../index.html">Blog</a>
<ul class="navbar-nav ms-auto">
<li><a class="nav-link active" href="../index.html" aria-current="page"><span class="menu-text">記事</span></a></li>
<li><a class="nav-link" href="../tags/"><span class="menu-text">タグ</span></a></li>
<li><a class="nav-link" href="../index.xml"><span class="menu-text">RSS</span></a></li>
</ul></nav></header><main>Content</main>
<footer><a href="../index.xml">RSS</a></footer></body></html>'''


def config(page):
    return json.loads(re.search(r'<script id="blog-language"[^>]*>(.*?)</script>', page)[1])


class LocalizationTest(unittest.TestCase):
    def test_both_versions_link_to_each_other(self):
        published = {"posts/example/index.html", "en/posts/example/index.html"}
        ja = localize("posts/example/index.html", PAGE, published)
        en = localize("en/posts/example/index.html", PAGE, published)
        self.assertEqual(config(ja)["pages"]["en"], "../../en/posts/example/")
        self.assertEqual(config(en)["pages"]["ja"], "../../../posts/example/")
        self.assertIn('data-translated="true"', en)
        self.assertIn('href="../../tags/"', en)
        self.assertIn('href="../../../index.xml"', en)

    def test_missing_translation_has_no_alternate_or_redirect_target(self):
        page = localize("posts/example/index.html", PAGE, {"posts/example/index.html"})
        self.assertEqual(config(page)["pages"], {"ja": "./"})
        self.assertNotIn('rel="alternate" hreflang="en"', page)
        self.assertIn('href="../../en/?lang=en"', page)
        self.assertIn('data-translated="false"', page)

    def test_navigation_is_english_without_client_side_javascript(self):
        page = localize("en/tags/index.html", PAGE, {"tags/index.html", "en/tags/index.html"})
        self.assertIn('<span class="menu-text">Posts</span>', page)
        self.assertIn('href="./" aria-current="page"><span class="menu-text">Tags</span>', page)
        self.assertIn('href="../"', page)
        self.assertNotIn('>記事<', page)
        self.assertNotIn('>タグ<', page)

    def test_repeated_preview_does_not_duplicate_controls_or_metadata(self):
        published = {"index.html", "en/index.html"}
        page = localize("en/index.html", PAGE, published)
        page = localize("en/index.html", page, published)
        self.assertEqual(page.count('id="blog-language"'), 1)
        self.assertEqual(page.count('data-language="ja"'), 1)
        self.assertEqual(page.count('hreflang="en"'), 1)

    def test_relative_paths_work_for_nested_pages_and_same_page(self):
        self.assertEqual(relative_url("en/index.html", "index.html"), "../")
        self.assertEqual(relative_url("en/tags/index.html", "en/tags/index.html"), "./")
        self.assertEqual(relative_url("en/posts/example/index.html", "en/index.html"), "../../")


if __name__ == "__main__":
    unittest.main()
