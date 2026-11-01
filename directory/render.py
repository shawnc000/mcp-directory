"""Render the bilingual static site from fetched GitHub facts."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from directory.copy import (
    CATEGORIES,
    FEATURED,
    ISSUE_FORM,
    METHODOLOGY,
    SOURCE_REPO,
    SUBMIT,
    category_by_id,
    t,
)
from directory.explain import activity_sentence, license_sentence, star_sentence, total_sentence
from directory.model import Tool
from directory.score import FORMULA_VERSION, score_breakdown
from directory.security import assess, assessment_lines
from directory.textutil import esc, mostly_chinese

BANNED_PHRASES = (
    "gumroad",
    "lemonsqueezy",
    "lemon squeezy",
    "buy.stripe.com",
    "checkout.stripe.com",
    "$49",
    "$19",
    "立即购买",
    "付款链接",
    "add to cart",
    "购物车",
)

LANGS = ("en", "zh")


class Site:
    def __init__(self, origin: str, base: str, fetched_at: datetime, tools: list[Tool]):
        self.origin = origin.rstrip("/")
        self.base = base.rstrip("/")
        if self.base == "/":
            self.base = ""
        self.fetched_at = fetched_at.astimezone(timezone.utc).replace(microsecond=0)
        self.fetched_stamp = self.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.tools = tools

    def href(self, path: str) -> str:
        if not path.startswith("/"):
            raise ValueError(path)
        return f"{self.base}{path}"

    def abs(self, path: str) -> str:
        return f"{self.origin}{self.href(path)}"


def localized(lang: str, path: str) -> str:
    """`path` is the Chinese URL. English pages live under /en/."""
    if lang == "zh":
        return path
    if path == "/":
        return "/en/"
    return "/en" + path


def split_lang(path: str) -> tuple[str, str]:
    if path == "/en" or path == "/en/":
        return "/", "/en/"
    if path.startswith("/en/"):
        zh = path[3:]
        if not zh.startswith("/"):
            zh = "/" + zh
        return zh, path
    en = "/en/" if path == "/" else "/en" + path
    return path, en


def disk_path(path: str) -> Path:
    if path == "/":
        return Path("index.html")
    return Path(path.strip("/")) / "index.html"


def _fmt_int(value: int | None, lang: str) -> str:
    if value is None:
        return t(lang, "not_in_snapshot")
    return f"{value:,}"


def _day(value: str | None) -> str:
    if not value:
        return "—"
    return value[:10]


def _license(tool: Tool, lang: str) -> str:
    if tool.license_spdx:
        return tool.license_spdx
    return t(lang, "none")


def _search_blob(tool: Tool) -> str:
    category = category_by_id(tool.category)
    return tool.search_blob(category["en"], category["zh"])


def _json_ld(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return f'<script type="application/ld+json">{payload}</script>'


def _chrome(site: Site, lang: str, path: str, title: str, description: str, body: str, json_ld: dict | None = None) -> str:
    zh_path, en_path = split_lang(path)
    en_url = site.abs(en_path)
    zh_url = site.abs(zh_path)
    canonical = site.abs(path)
    home = site.href(localized(lang, "/"))
    css = site.href("/assets/style.css")
    icon = site.href("/assets/favicon.svg")
    other = "zh" if lang == "en" else "en"
    other_path = zh_path if lang == "en" else en_path
    other_label = "中文" if lang == "en" else "English"
    ld = _json_ld(json_ld) if json_ld else ""
    nav = [
        (localized(lang, "/"), t(lang, "nav_home")),
        (localized(lang, "/methodology/"), t(lang, "nav_method")),
        (localized(lang, "/submit/"), t(lang, "nav_submit")),
        (localized(lang, "/featured/"), t(lang, "nav_featured")),
    ]
    nav_html = "".join(
        f'<a href="{esc(site.href(href))}"' + (' aria-current="page"' if href == path else "") + f">{esc(label)}</a>"
        for href, label in nav
    )
    return f"""<!DOCTYPE html>
<html lang="{esc(t(lang, "html_lang"))}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<link rel="alternate" hreflang="en" href="{esc(en_url)}">
<link rel="alternate" hreflang="zh-Hans" href="{esc(zh_url)}">
<link rel="alternate" hreflang="x-default" href="{esc(zh_url)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="{'zh_CN' if lang == 'zh' else 'en_US'}">
<link rel="icon" href="{esc(icon)}" type="image/svg+xml">
<link rel="stylesheet" href="{esc(css)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=Noto+Sans+SC:wght@400;600;700&display=swap" rel="stylesheet">
{ld}
</head>
<body>
<a class="skip" href="#content">{esc(t(lang, "skip"))}</a>
<header class="top">
  <div class="top-inner">
    <a class="brand" href="{esc(home)}">
      <span class="seal" aria-hidden="true">MCP</span>
      <span>
        <strong>{esc(t(lang, "site_name"))}</strong>
        <small>{esc(t(lang, "tagline"))}</small>
      </span>
    </a>
    <nav class="nav" aria-label="primary">{nav_html}</nav>
    <div class="tools">
      <form class="search" action="{esc(home)}" method="get" role="search">
        <label class="sr-only" for="q">{esc(t(lang, "search_label"))}</label>
        <input id="q" name="q" type="search" placeholder="{esc(t(lang, "search_placeholder"))}" autocomplete="off">
      </form>
      <a class="lang" href="{esc(site.href(other_path))}" hreflang="{esc(t(other, "html_lang"))}" lang="{esc(t(other, "html_lang"))}">{esc(other_label)}</a>
    </div>
  </div>
</header>
<main id="content">
{body}
</main>
<footer class="foot">
  <p>{esc(t(lang, "footer_note"))}</p>
  <p>{esc(t(lang, "updated_label"))} <time datetime="{esc(site.fetched_stamp)}">{esc(site.fetched_stamp)}</time>
     · {esc(t(lang, "formula_label"))} v{esc(FORMULA_VERSION)}</p>
  <p>
    <a href="{esc(site.href("/catalog.json"))}">{esc(t(lang, "download"))}</a>
    · <a href="https://github.com/{esc(SOURCE_REPO)}">{esc(t(lang, "github_repo"))}</a>
  </p>
</footer>
<script>
(function () {{
  var rows = document.querySelectorAll("[data-search]");
  if (!rows.length) return;
  var input = document.getElementById("q");
  var count = document.getElementById("result-count");
  var empty = document.getElementById("empty-search");
  function apply() {{
    var needle = input.value.trim().toLowerCase();
    var shown = 0;
    rows.forEach(function (row) {{
      var ok = !needle || (row.getAttribute("data-search") || "").indexOf(needle) !== -1;
      row.hidden = !ok;
      if (ok) shown += 1;
    }});
    if (count) count.textContent = String(shown);
    if (empty) empty.hidden = shown !== 0;
  }}
  input.addEventListener("input", function () {{
    var url = new URL(window.location.href);
    if (input.value) url.searchParams.set("q", input.value);
    else url.searchParams.delete("q");
    history.replaceState(null, "", url);
    apply();
  }});
  var initial = new URLSearchParams(window.location.search).get("q");
  if (initial) input.value = initial;
  apply();
}})();
</script>
</body>
</html>
"""


def _table(site: Site, lang: str, tools: list[Tool], include_category: bool) -> str:
    heads = [
        t(lang, "col_score"),
        t(lang, "col_tool"),
        t(lang, "col_stars"),
        t(lang, "col_push"),
        t(lang, "col_license"),
    ]
    if include_category:
        heads.append(t(lang, "col_category"))
    head_html = "".join(f"<th scope=\"col\">{esc(name)}</th>" for name in heads)
    rows = []
    for tool in tools:
        category = category_by_id(tool.category)
        cat_label = category["zh"] if lang == "zh" else category["en"]
        description = tool.description or t(lang, "no_description")
        cat_cell = ""
        if include_category:
            cat_cell = (
                f'<td><a href="{esc(site.href(localized(lang, f"/categories/{tool.category}/")))}">'
                f"{esc(cat_label)}</a></td>"
            )
        rows.append(
            f"""<tr data-search="{esc(_search_blob(tool))}">
<td class="num">{tool.breakdown.total}</td>
<td><a href="{esc(site.href(localized(lang, f"/tools/{tool.slug}/")))}">{esc(tool.full_name)}</a>
<span class="dek">{esc(description)}</span></td>
<td class="num">{_fmt_int(tool.stars, lang)}</td>
<td class="num">{esc(_day(tool.pushed_at))}</td>
<td>{esc(_license(tool, lang))}</td>
{cat_cell}
</tr>"""
        )
    caption = t(lang, "all_title") if include_category else ""
    cap = f"<caption class=\"sr-only\">{esc(caption)}</caption>" if caption else ""
    return f"<div class=\"sheet\"><table>{cap}<thead><tr>{head_html}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def _home(site: Site, lang: str) -> str:
    path = localized(lang, "/")
    items = "".join(f"<li><strong>{esc(title)}</strong><span>{esc(text)}</span></li>" for title, text in t(lang, "how_items"))
    cards = []
    for category in CATEGORIES:
        count = sum(1 for tool in site.tools if tool.category == category["id"])
        label = category["zh"] if lang == "zh" else category["en"]
        blurb = category["blurb_zh"] if lang == "zh" else category["blurb_en"]
        cards.append(
            f"""<a class="cat" href="{esc(site.href(localized(lang, f"/categories/{category['id']}/")))}">
<strong>{esc(label)}</strong><em>{count}</em><span>{esc(blurb)}</span></a>"""
        )
    total = len(site.tools)
    body = f"""
<section class="hero">
  <h1>{esc(t(lang, "hero_title"))}</h1>
  <p>{esc(t(lang, "hero_p1"))}</p>
  <p>{esc(t(lang, "hero_p2"))}</p>
</section>
<section>
  <h2>{esc(t(lang, "how_title"))}</h2>
  <ol class="steps">{items}</ol>
</section>
<section class="soon" id="featured">
  <p class="kicker">{esc(t(lang, "featured_kicker"))}</p>
  <h2>{esc(t(lang, "featured_title"))}</h2>
  <p>{esc(t(lang, "featured_p"))}</p>
  <p><a href="{esc(site.href(localized(lang, "/featured/")))}">{esc(t(lang, "featured_link"))}</a></p>
</section>
<section>
  <h2>{esc(t(lang, "categories_title"))}</h2>
  <div class="cats">{''.join(cards)}</div>
</section>
<section>
  <div class="section-head">
    <h2>{esc(t(lang, "all_title"))}</h2>
    <p class="count">{esc(t(lang, "result_of"))} <span id="result-count">{total}</span> {esc(t(lang, "result_mid"))} {total}</p>
  </div>
  <p id="empty-search" class="empty" hidden>{esc(t(lang, "empty"))}</p>
  {_table(site, lang, site.tools, True)}
</section>
"""
    title = f"{t(lang, 'site_name')} — {t(lang, 'tagline')}"
    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": t(lang, "site_name"),
        "url": site.abs(path),
        "description": t(lang, "hero_p2"),
        "inLanguage": ["en", "zh-Hans"],
    }
    return _chrome(site, lang, path, title, t(lang, "hero_p2"), body, data)


def _category(site: Site, lang: str, category: dict) -> str:
    path = localized(lang, f"/categories/{category['id']}/")
    label = category["zh"] if lang == "zh" else category["en"]
    essays = category["essay_zh"] if lang == "zh" else category["essay_en"]
    paragraphs = "".join(f"<p>{esc(paragraph)}</p>" for paragraph in essays)
    tools = [tool for tool in site.tools if tool.category == category["id"]]
    body = f"""
<p class="crumb"><a href="{esc(site.href(localized(lang, "/")))}">{esc(t(lang, "back"))}</a></p>
<h1>{esc(label)}</h1>
<p class="kicker">{esc(t(lang, "editorial"))}</p>
{paragraphs}
<h2>{esc(t(lang, "all_title"))}</h2>
{_table(site, lang, tools, False) if tools else f"<p>{esc(t(lang, 'empty'))}</p>"}
"""
    description = category["blurb_zh"] if lang == "zh" else category["blurb_en"]
    title = f"{label} — {t(lang, 'site_name')}"
    return _chrome(site, lang, path, title, description, body)


def _meter(tool: Tool) -> str:
    b = tool.breakdown
    return (
        '<div class="meter" aria-hidden="true">'
        f'<span class="meter-star" style="width:{b.star_points:.2f}%"></span>'
        f'<span class="meter-act" style="width:{b.activity_points:.2f}%"></span>'
        f'<span class="meter-lic" style="width:{b.license_points:.2f}%"></span>'
        "</div>"
    )


def _tool(site: Site, lang: str, tool: Tool) -> str:
    path = localized(lang, f"/tools/{tool.slug}/")
    category = category_by_id(tool.category)
    cat_label = category["zh"] if lang == "zh" else category["en"]
    b = tool.breakdown
    description = tool.description or t(lang, "no_description")
    title_line = ""
    if tool.readme_title and tool.readme_title.lower() != tool.full_name.lower():
        title_line = f"<p class=\"dek\">{esc(t(lang, 'readme_title_label'))}: {esc(tool.readme_title)}</p>"
    if tool.readme_excerpt:
        excerpt = f"<pre class=\"excerpt\">{esc(tool.readme_excerpt)}</pre>"
    else:
        reason = tool.readme_error or t(lang, "no_excerpt")
        excerpt = f"<p>{esc(t(lang, 'no_excerpt'))} ({esc(reason)})</p>"
    homepage = ""
    if tool.homepage:
        homepage = f"<div><dt>{esc(t(lang, 'homepage_label'))}</dt><dd><a href=\"{esc(tool.homepage)}\">{esc(tool.homepage)}</a></dd></div>"
    topics = ", ".join(tool.topics[:12]) if tool.topics else t(lang, "none")
    related = [other for other in site.tools if other.category == tool.category and other.full_name != tool.full_name]
    related_html = "".join(
        f'<li><a href="{esc(site.href(localized(lang, f"/tools/{other.slug}/")))}">{esc(other.full_name)}</a> '
        f'<span class="num">{other.breakdown.total}</span></li>'
        for other in related
    )
    issue = f"{ISSUE_FORM}&title=Correction%3A%20{tool.full_name.replace('/', '%2F')}"
    assessment = assess(b, tool.archived, tool.readme_excerpt, tool.data_source)
    assessment_html = "".join(f"<li>{esc(line)}</li>" for line in assessment_lines(assessment, lang))
    translation = ""
    if tool.desc_zh:
        translation = (
            f"<h2>{esc(t(lang, 'translation_label'))}</h2>"
            f"<p>{esc(t(lang, 'translation_note'))}</p>"
            f"<p>{esc(tool.desc_zh)}</p>"
        )
    elif lang == "zh" and mostly_chinese(tool.description):
        translation = f"<p>{esc(t(lang, 'zh_original_note'))}</p>"
    elif lang == "zh":
        translation = f"<p>{esc(t(lang, 'no_translation_note'))}</p>"
    if tool.archived is None:
        archived_label = t(lang, "not_in_snapshot")
    else:
        archived_label = t(lang, "yes") if tool.archived else t(lang, "no")
    extra_related = ""
    if len(related) > 24:
        extra_related = (
            f'<p><a href="{esc(site.href(localized(lang, f"/categories/{tool.category}/")))}">'
            f"{esc(cat_label)} ({len(related)})</a></p>"
        )
        related_html = "".join(
            f'<li><a href="{esc(site.href(localized(lang, f"/tools/{other.slug}/")))}">{esc(other.full_name)}</a> '
            f'<span class="num">{other.breakdown.total}</span></li>'
            for other in related[:24]
        )
    body = f"""
<p class="crumb"><a href="{esc(site.href(localized(lang, "/")))}">{esc(t(lang, "back"))}</a>
 · <a href="{esc(site.href(localized(lang, f"/categories/{tool.category}/")))}">{esc(cat_label)}</a></p>
<h1>{esc(tool.full_name)}</h1>
{title_line}
<p class="kicker">{esc(t(lang, "original_label"))}</p>
<blockquote class="quote"><p>{esc(description)}</p></blockquote>
{translation}
<p><a href="{esc(tool.html_url)}">{esc(tool.html_url)}</a></p>
<section class="security">
  <h2>{esc(t(lang, "security_title"))}</h2>
  <p>{esc(t(lang, "security_note"))}</p>
  <ul class="assessment">{assessment_html}</ul>
</section>
<section class="score">
  <p class="score-total"><span>{b.total}</span><small>/ 100</small></p>
  <p class="kicker">{esc(t(lang, "formula_label"))} v{esc(FORMULA_VERSION)}</p>
  {_meter(tool)}
  <dl class="parts">
    <div><dt>{esc(t(lang, "star_points"))}</dt><dd>{esc(star_sentence(b, lang))}</dd></div>
    <div><dt>{esc(t(lang, "activity_points"))}</dt><dd>{esc(activity_sentence(b, lang))}</dd></div>
    <div><dt>{esc(t(lang, "license_points"))}</dt><dd>{esc(license_sentence(b, lang))}</dd></div>
    <div><dt>{esc(t(lang, "total_points"))}</dt><dd>{esc(total_sentence(b, lang))}</dd></div>
  </dl>
  <p>{esc(t(lang, "updated_label"))} <time datetime="{esc(b.fetched_at)}">{esc(b.fetched_at)}</time></p>
</section>
<section>
  <h2>{esc(t(lang, "facts_title"))}</h2>
  <dl class="facts">
    <div><dt>{esc(t(lang, "col_stars"))}</dt><dd>{_fmt_int(tool.stars, lang)}</dd></div>
    <div><dt>{esc(t(lang, "forks_label"))}</dt><dd>{_fmt_int(tool.forks, lang)}</dd></div>
    <div><dt>{esc(t(lang, "open_issues_label"))}</dt><dd>{_fmt_int(tool.open_issues, lang)}</dd></div>
    <div><dt>{esc(t(lang, "watchers_label"))}</dt><dd>{_fmt_int(tool.watchers, lang)}</dd></div>
    <div><dt>{esc(t(lang, "language_label"))}</dt><dd>{esc(tool.language or t(lang, "none"))}</dd></div>
    <div><dt>{esc(t(lang, "col_license"))}</dt><dd>{esc(tool.license_name or t(lang, "none"))} ({esc(_license(tool, lang))})</dd></div>
    <div><dt>{esc(t(lang, "pushed_label"))}</dt><dd>{esc(tool.pushed_at or t(lang, "none"))}</dd></div>
    <div><dt>{esc(t(lang, "updated_at_label"))}</dt><dd>{esc(tool.updated_at or t(lang, "none"))}</dd></div>
    <div><dt>{esc(t(lang, "created_label"))}</dt><dd>{esc(tool.created_at or t(lang, "none"))}</dd></div>
    <div><dt>{esc(t(lang, "branch_label"))}</dt><dd>{esc(tool.default_branch)}</dd></div>
    <div><dt>{esc(t(lang, "archived_label"))}</dt><dd>{esc(archived_label)}</dd></div>
    <div><dt>{esc(t(lang, "topics_label"))}</dt><dd>{esc(topics)}</dd></div>
    <div><dt>{esc(t(lang, "editorial"))}</dt><dd><a href="{esc(site.href(localized(lang, f"/categories/{tool.category}/")))}">{esc(cat_label)}</a></dd></div>
    {homepage}
  </dl>
</section>
<section>
  <h2>{esc(t(lang, "excerpt_title"))}</h2>
  <p>{esc(t(lang, "excerpt_note"))}</p>
  {excerpt}
</section>
<section>
  <h2>{esc(t(lang, "not_a_review_title"))}</h2>
  <p>{esc(t(lang, "not_a_review"))}</p>
  <p><a href="{esc(issue)}">{esc(t(lang, "correction"))}</a></p>
</section>
<section>
  <h2>{esc(t(lang, "related_title"))}</h2>
  <ul class="related">{related_html}</ul>
  {extra_related}
</section>
"""
    meta = f"{tool.full_name}: {description} Score {b.total}/100. Fetched {b.fetched_at}."
    page_title = f"{tool.full_name} — {b.total}/100 | {t(lang, 'site_name')}"
    ld = {
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "name": tool.full_name,
        "codeRepository": tool.html_url,
        "url": site.abs(path),
        "programmingLanguage": tool.language,
        "dateModified": tool.pushed_at,
        "description": tool.description,
    }
    if tool.license_spdx and tool.license_spdx != "NOASSERTION":
        ld["license"] = f"https://spdx.org/licenses/{tool.license_spdx}.html"
    ld = {key: value for key, value in ld.items() if value}
    return _chrome(site, lang, path, page_title, meta[:300], body, ld)


def _examples(lang: str) -> str:
    fetched = datetime(2026, 1, 31, tzinfo=timezone.utc)
    recent = (fetched - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    stale = (fetched - timedelta(days=200)).strftime("%Y-%m-%dT%H:%M:%SZ")
    first = score_breakdown(100, recent, "MIT", fetched)
    second = score_breakdown(10000, stale, None, fetched)
    blocks = []
    for breakdown, stars, license_id in (
        (first, 100, "MIT"),
        (second, 10000, "empty"),
    ):
        blocks.append(
            "<section class=\"example\">"
            f"<h3>{stars} stars, license {esc(license_id)}, fetched {esc(breakdown.fetched_at)}</h3>"
            f"<p>{esc(star_sentence(breakdown, lang))}</p>"
            f"<p>{esc(activity_sentence(breakdown, lang))}</p>"
            f"<p>{esc(license_sentence(breakdown, lang))}</p>"
            f"<p>{esc(total_sentence(breakdown, lang))}</p>"
            "</section>"
        )
    return "".join(blocks)


def _prose_page(site: Site, lang: str, path: str, title: str, description: str, paragraphs: list[str], extra: str = "") -> str:
    body = f"<h1>{esc(title)}</h1>" + "".join(f"<p>{esc(paragraph)}</p>" for paragraph in paragraphs) + extra
    return _chrome(site, lang, localized(lang, path), f"{title} — {t(lang, 'site_name')}", description, body)


def _methodology(site: Site, lang: str) -> str:
    extra = (
        f"<h2>{esc(t(lang, 'example_title'))}</h2>"
        f"<p>{esc(t(lang, 'example_note'))}</p>"
        + _examples(lang)
    )
    return _prose_page(
        site,
        lang,
        "/methodology/",
        t(lang, "method_title"),
        t(lang, "method_desc"),
        METHODOLOGY[lang],
        extra,
    )


def _submit(site: Site, lang: str) -> str:
    extra = f'<p><a class="button" href="{esc(ISSUE_FORM)}">{esc(t(lang, "issue_link"))}</a></p>'
    return _prose_page(site, lang, "/submit/", t(lang, "submit_title"), t(lang, "submit_desc"), SUBMIT[lang], extra)


def _featured(site: Site, lang: str) -> str:
    paragraphs = "".join(f"<p>{esc(paragraph)}</p>" for paragraph in FEATURED[lang])
    body = (
        f'<p class="kicker">{esc(t(lang, "featured_kicker"))}</p>'
        f"<h1>{esc(t(lang, 'featured_page_title'))}</h1>"
        f"{paragraphs}"
        f'<p><a class="button" href="{esc(site.href(localized(lang, "/submit/")))}">{esc(t(lang, "nav_submit"))}</a></p>'
    )
    return _chrome(
        site,
        lang,
        localized(lang, "/featured/"),
        f"{t(lang, 'featured_page_title')} — {t(lang, 'site_name')}",
        t(lang, "featured_page_desc"),
        body,
    )


def _not_found(site: Site) -> str:
    body = """
<h1>404</h1>
<p><a href="{zh}" lang="zh-Hans">MCP 目录</a> · <a href="{en}">English</a></p>
""".format(zh=esc(site.href("/")), en=esc(site.href("/en/")))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>404 — MCP Directory</title>
<meta name="robots" content="noindex"><link rel="stylesheet" href="{esc(site.href("/assets/style.css"))}">
</head><body><main id="content">{body}</main></body></html>"""


def _sitemap(site: Site) -> str:
    paths = ["/"]
    for suffix in ("/methodology/", "/submit/", "/featured/"):
        paths.append(suffix)
    for category in CATEGORIES:
        paths.append(f"/categories/{category['id']}/")
    for tool in site.tools:
        paths.append(f"/tools/{tool.slug}/")
    urls = []
    lastmod = site.fetched_stamp[:10]
    for path in paths:
        zh = site.abs(path)
        en = site.abs(localized("en", path))
        for loc, alt_en, alt_zh in ((en, en, zh), (zh, en, zh)):
            urls.append(
                "  <url>\n"
                f"    <loc>{esc(loc)}</loc>\n"
                f"    <lastmod>{lastmod}</lastmod>\n"
                f'    <xhtml:link rel="alternate" hreflang="en" href="{esc(alt_en)}"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="zh-Hans" href="{esc(alt_zh)}"/>\n'
                "  </url>"
            )
    body = "\n".join(urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        f"{body}\n</urlset>\n"
    )


def _robots(site: Site) -> str:
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {site.abs('/sitemap.xml')}\n"
    )


def _catalog_dump(site: Site) -> str:
    tools = []
    for tool in site.tools:
        b = tool.breakdown
        tools.append(
            {
                "repo": tool.full_name,
                "category": tool.category,
                "description": tool.description,
                "homepage": tool.homepage,
                "html_url": tool.html_url,
                "stars": tool.stars,
                "forks": tool.forks,
                "open_issues_including_pull_requests": tool.open_issues,
                "watchers": tool.watchers,
                "language": tool.language,
                "topics": list(tool.topics),
                "license_spdx": tool.license_spdx,
                "license_name": tool.license_name,
                "pushed_at": tool.pushed_at,
                "updated_at": tool.updated_at,
                "created_at": tool.created_at,
                "archived": tool.archived,
                "default_branch": tool.default_branch,
                "readme_title": tool.readme_title,
                "readme_excerpt": tool.readme_excerpt,
                "score": {
                    "formula_version": FORMULA_VERSION,
                    "total": b.total,
                    "star_raw": round(b.star_raw, 4),
                    "star_points": round(b.star_points, 4),
                    "activity_points": b.activity_points,
                    "days_since_push": b.days_since_push,
                    "license_points": b.license_points,
                    "license_spdx": b.license_spdx,
                    "fetched_at": b.fetched_at,
                },
            }
        )
    return json.dumps(
        {
            "fetched_at": site.fetched_stamp,
            "formula_version": FORMULA_VERSION,
            "tool_count": len(tools),
            "tools": tools,
        },
        ensure_ascii=False,
        indent=2,
    )


def _write(root: Path, path: str, text: str) -> None:
    dest = root / disk_path(path) if path.endswith("/") or path == "/" else root / path.lstrip("/")
    if path in {"/", "/zh/"} or path.endswith("/"):
        dest = root / disk_path(path)
    else:
        dest = root / path.lstrip("/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def render_site(site: Site, root: Path, assets: Path, min_tools: int = 50) -> None:
    if len(site.tools) < min_tools:
        raise SystemExit(f"refusing to render {len(site.tools)} tools; need at least {min_tools}")
    root.mkdir(parents=True, exist_ok=True)
    (root / "assets").mkdir(exist_ok=True)
    (root / "assets" / "style.css").write_text((assets / "style.css").read_text(encoding="utf-8"), encoding="utf-8")
    (root / "assets" / "favicon.svg").write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
<rect width="32" height="32" rx="6" fill="#8f2d14"/>
<text x="16" y="21" text-anchor="middle" font-family="Georgia" font-size="12" fill="#fff7ef">MCP</text>
</svg>
""",
        encoding="utf-8",
    )
    pages: list[tuple[str, str]] = []
    for lang in LANGS:
        pages.append((localized(lang, "/"), _home(site, lang)))
        pages.append((localized(lang, "/methodology/"), _methodology(site, lang)))
        pages.append((localized(lang, "/submit/"), _submit(site, lang)))
        pages.append((localized(lang, "/featured/"), _featured(site, lang)))
        for category in CATEGORIES:
            pages.append((localized(lang, f"/categories/{category['id']}/"), _category(site, lang, category)))
        for tool in site.tools:
            pages.append((localized(lang, f"/tools/{tool.slug}/"), _tool(site, lang, tool)))
    for path, html in pages:
        _write(root, path, html)
    (root / "404.html").write_text(_not_found(site), encoding="utf-8")
    (root / "sitemap.xml").write_text(_sitemap(site), encoding="utf-8")
    (root / "robots.txt").write_text(_robots(site), encoding="utf-8")
    (root / "catalog.json").write_text(_catalog_dump(site) + "\n", encoding="utf-8")
    _validate(root, site)


def _validate(root: Path, site: Site) -> None:
    authored = []
    for lang in LANGS:
        for path in ("/", "/methodology/", "/submit/", "/featured/"):
            authored.append(root / disk_path(localized(lang, path)))
        for category in CATEGORIES:
            authored.append(root / disk_path(localized(lang, f"/categories/{category['id']}/")))
    blob = "\n".join(path.read_text(encoding="utf-8") for path in authored).lower()
    for phrase in BANNED_PHRASES:
        if phrase.lower() in blob:
            raise SystemExit(f"banned phrase in site output: {phrase}")
    en_featured = (root / "en" / "featured" / "index.html").read_text(encoding="utf-8")
    zh_featured = (root / "featured" / "index.html").read_text(encoding="utf-8")
    if "Coming soon" not in en_featured:
        raise SystemExit("English featured page is missing Coming soon")
    if "即将推出" not in zh_featured:
        raise SystemExit("Chinese featured page is missing 即将推出")
    robots = (root / "robots.txt").read_text(encoding="utf-8")
    if f"Sitemap: {site.abs('/sitemap.xml')}" not in robots:
        raise SystemExit("robots.txt is missing the sitemap URL")
    sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
    for tool in site.tools:
        for lang in LANGS:
            page = root / disk_path(localized(lang, f"/tools/{tool.slug}/"))
            text = page.read_text(encoding="utf-8")
            if tool.full_name not in text or "log10" not in text or tool.breakdown.fetched_at not in text:
                raise SystemExit(f"tool page missing score details: {page}")
            if lang == "zh" and "公开安全评估" not in text:
                raise SystemExit(f"tool page missing security assessment: {page}")
            if lang == "en" and "Security assessment" not in text:
                raise SystemExit(f"tool page missing security assessment: {page}")
            if str(tool.breakdown.total) not in text:
                raise SystemExit(f"tool page missing total: {page}")
        if site.abs(f"/tools/{tool.slug}/") not in sitemap:
            raise SystemExit(f"sitemap missing {tool.full_name}")
    if "<script>alert" in blob:
        raise SystemExit("unescaped script in generated HTML")
