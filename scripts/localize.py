"""Localize Quarto's shared navigation and link only published translations.

Run by Quarto after rendering. Japanese paths stay unchanged; English pages
live at en/<same path>. Only HTML in the output directory is modified.
"""

import html
import json
import os
from pathlib import Path
import posixpath
import re


MARKER = re.compile(r"<!-- blog-language:start -->.*?<!-- blog-language:end -->", re.S)


def relative_url(source, target):
    path = posixpath.relpath(target, posixpath.dirname(source) or ".")
    # Use directory URLs, matching existing public article links.
    return path.removesuffix("index.html") or "./"


def localize(source, document, published):
    en = source.startswith("en/")
    lang = "en" if en else "ja"
    key = source.removeprefix("en/") if en else source
    candidates = {"ja": key, "en": "en/" + key}
    pages = {locale: relative_url(source, path)
             for locale, path in candidates.items() if path in published}
    home = relative_url(source, "en/index.html" if en else "index.html")
    tags = relative_url(source, "en/tags/index.html" if en else "tags/index.html")
    # The existing RSS feed contains Japanese articles; keep its stable URL.
    feed = posixpath.relpath("index.xml", posixpath.dirname(source) or ".")
    config = {"language": lang, "pages": pages}
    head = ['<!-- blog-language:start -->']
    for locale, href in pages.items():
        head.append(f'<link rel="alternate" hreflang="{locale}" href="{html.escape(href, quote=True)}">')
    head.append('<script id="blog-language" type="application/json">'
                + json.dumps(config, ensure_ascii=True).replace("<", "\\u003c") + '</script>')
    script = posixpath.relpath("assets/language.js", posixpath.dirname(source) or ".")
    head.append(f'<script src="{html.escape(script, quote=True)}"></script>')
    head.append('<!-- blog-language:end -->')
    document = MARKER.sub("", document)
    # Select the language before rendering the body or loading other scripts.
    document = re.sub(r'(<meta charset="[^"]+">)',
                      lambda m: m[0] + "\n" + "\n".join(head), document, count=1)

    other = "ja" if en else "en"
    target = pages.get(other, relative_url(source, "index.html" if en else "en/index.html"))
    label = "日本語" if en else "English"
    title = ("Read this page in Japanese" if en else "このページを英語で読む") if other in pages else (
        "Browse posts in Japanese" if en else "英語版の記事一覧へ")
    switch = (f'<li class="nav-item language-switcher"><a class="nav-link" '
              f'href="{html.escape(target, quote=True)}?lang={other}" lang="{other}" '
              f'hreflang="{other}" data-language="{other}" '
              f'data-translated="{str(other in pages).lower()}" title="{title}">{label}</a></li>')

    def navigation(match):
        nav = match[0]
        # Idempotence matters for preview and incremental renders.
        nav = re.sub(r'<li class="nav-item language-switcher">.*?</li>', '', nav, flags=re.S)
        nav = re.sub(r'(<a class="navbar-brand" href=")[^"]*(")',
                     lambda m: m[1] + html.escape(home, quote=True) + m[2], nav)
        labels = {"記事": ("Posts" if en else "記事", home),
                  "Posts": ("Posts" if en else "記事", home),
                  "タグ": ("Tags" if en else "タグ", tags),
                  "Tags": ("Tags" if en else "タグ", tags),
                  "RSS": ("RSS", feed)}

        def link(m):
            label, href = labels[m[1]]
            active = (label in ("記事", "Posts") and key == "index.html"
                      or label in ("タグ", "Tags") and key == "tags/index.html")
            current = ' aria-current="page"' if active else ''
            return (f'<a class="nav-link{" active" if active else ""}" '
                    f'href="{html.escape(href, quote=True)}"{current}>'
                    f'<span class="menu-text">{label}</span></a>')

        nav = re.sub(r'<a class="nav-link[^\"]*"[^>]*>\s*<span class="menu-text">'
                     r'(記事|Posts|タグ|Tags|RSS)</span></a>', link, nav)
        nav = re.sub(r'(<ul class="navbar-nav[^\"]*ms-auto">.*?)(</ul>)',
                     lambda m: m[1] + switch + m[2], nav, count=1, flags=re.S)
        if 'data-language=' not in nav:
            raise ValueError(f"Could not find Quarto navigation in {source}")
        return nav

    document = re.sub(r'<header id="quarto-header".*?</header>', navigation, document, count=1, flags=re.S)

    def footer(match):
        return re.sub(r'href="[^"]*index.xml"', f'href="{feed}"', match[0])

    document = re.sub(r'<footer\b.*?</footer>', footer, document, flags=re.S)
    return document


def main():
    output = Path(os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "_site"))
    documents = {}
    for path in output.rglob("*.html"):
        document = path.read_text(encoding="utf-8")
        if 'id="quarto-header"' in document:
            documents[path.relative_to(output).as_posix()] = document
    for source, document in documents.items():
        (output / source).write_text(localize(source, document, documents), encoding="utf-8")


if __name__ == "__main__":
    main()
