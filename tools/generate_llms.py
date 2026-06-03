#!/usr/bin/env python3
"""
Generate llms.txt (short index) and llms-full.txt (entire site content) for
https://stillrot.github.io/ so that LLMs and AI agents can read & evaluate the
whole portfolio WITHOUT executing the site's JavaScript.

Why: the home page renders Publications/Patents/News/Research from data/*.json
via JS, so a plain fetch sees empty "Loading…" shells. This script bakes every
page's text, the link structure, the site map, and all JSON data into one
plain-text file.

Re-run after editing any site content:

    python3 tools/generate_llms.py

Outputs (written to the repo root): llms.txt, llms-full.txt
"""
import os
import re
import json
import html
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://stillrot.github.io"

# (disk path, URL path, title, one-line description) -- order = site map order
PAGES = [
    ("index.html", "/", "Home",
     "Profile, career overview, and tabbed publications / patents / news / research"),
    ("career/hdclabs/index.html", "/career/hdclabs/", "Career — HDC LABS",
     "Work & Activities timeline + fire / elevator / IP project deep-dives"),
    ("career/metaent/index.html", "/career/metaent/", "Career — Metaverse Entertainment",
     "TD Team, AI Part"),
    ("career/ku/index.html", "/career/ku/", "Career — Korea University",
     "M.S. in Electrical Engineering"),
    ("career/bu/index.html", "/career/bu/", "Career — Baekseok University",
     "B.S. in Multimedia Engineering"),
    ("cv/index.html", "/cv/", "CV", "Curriculum vitae"),
    ("portfolio2026/index.html", "/portfolio2026/", "Portfolio Deck (2026)",
     "Slide-deck narrative of the projects and research"),
]

SKIP = {"script", "style", "svg", "noscript", "head", "path", "g", "defs",
        "clippath", "lineargradient", "radialgradient", "stop", "circle",
        "rect", "polygon", "polyline", "line", "ellipse", "use", "symbol"}
HEADINGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}
BLOCK = {"p", "div", "section", "article", "header", "footer", "nav", "ul", "ol",
         "table", "tr", "figure", "figcaption", "blockquote", "main", "aside", "dl"}
# inline tags that should be space-separated so adjacent siblings don't glue together
INLINE_SEP = {"span", "a", "strong", "em", "b", "i", "code", "small", "sup", "sub",
              "label", "time", "abbr", "mark", "td", "th"}
DROP_LINES = {"loading…", "loading...", "loading"}


class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.buf = []
        self.skip = 0
        self.links = []        # (text, href)
        self.a_href = None
        self.a_txt = ""
        self.a_label = ""

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        a = dict(attrs)
        cls = a.get("class", "") or ""
        # keep Korean / English mirror blocks on separate lines (avoid concatenation)
        if "en-only" in cls or "ko-only" in cls:
            self.buf.append("\n")
        elif tag in INLINE_SEP:
            self.buf.append(" ")
        if tag in HEADINGS:
            self.buf.append("\n\n" + HEADINGS[tag] + " ")
        elif tag == "li":
            self.buf.append("\n- ")
        elif tag == "br":
            self.buf.append("\n")
            if self.a_href is not None:
                self.a_txt += " "
        elif tag == "img":
            alt = (a.get("alt") or "").strip()
            if alt:
                self.buf.append(" [image: %s] " % alt)
        elif tag in BLOCK:
            self.buf.append("\n")
        if tag == "a":
            self.a_href = a.get("href")
            self.a_txt = ""
            self.a_label = a.get("aria-label") or a.get("title") or ""

    def handle_startendtag(self, tag, attrs):
        if self.skip:
            return
        if tag == "br":
            self.buf.append("\n")
        elif tag == "img":
            alt = (dict(attrs).get("alt") or "").strip()
            if alt:
                self.buf.append(" [image: %s] " % alt)

    def handle_endtag(self, tag):
        if tag in SKIP:
            if self.skip:
                self.skip -= 1
            return
        if self.skip:
            return
        if tag in HEADINGS or tag in BLOCK:
            self.buf.append("\n")
        if tag == "a" and self.a_href is not None:
            label = re.sub(r"\s+", " ", self.a_txt).strip() or self.a_label
            self.links.append((label, self.a_href))
            self.a_href = None

    def handle_data(self, data):
        if self.skip:
            return
        if self.a_href is not None:
            self.a_txt += data
        self.buf.append(data)

    def result(self):
        s = html.unescape("".join(self.buf))
        s = re.sub(r"[ \t]+", " ", s)
        s = re.sub(r" *\n *", "\n", s)
        # pull a lone heading marker (#) or list bullet (-) onto its content line
        s = re.sub(r"(?m)^(#{1,6})\n+", r"\1 ", s)
        s = re.sub(r"(?m)^-\n+", "- ", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        kept = [ln for ln in s.split("\n") if ln.strip().lower() not in DROP_LINES]
        return "\n".join(kept).strip()


def extract_page(disk):
    with open(os.path.join(ROOT, disk), encoding="utf-8") as f:
        raw = f.read()
    p = Extract()
    p.feed(raw)
    return p.result(), p.links


def resolve(url_path, href):
    """Turn a page-relative href into an absolute site URL (best effort)."""
    if not href or href.startswith(("mailto:", "tel:", "javascript:")):
        return None
    if href.startswith("http"):
        return href
    if href.startswith("#"):
        return SITE + url_path + href
    base = SITE + url_path
    if href.startswith("/"):
        return SITE + href
    if href.startswith("./"):
        return base + href[2:]
    if href.startswith("../"):
        # collapse one directory level per ../
        cur = base.rstrip("/").rsplit("/", 1)[0]
        while href.startswith("../"):
            cur = cur.rsplit("/", 1)[0]
            href = href[3:]
        return cur + "/" + href
    return base + href


def links_block(url_path, links):
    seen = []
    internal, external = [], []
    for txt, href in links:
        full = resolve(url_path, href)
        if not full:
            continue
        key = (txt, full)
        if key in seen:
            continue
        seen.append(key)
        label = txt or "(no text)"
        row = "- %s -> %s" % (label, full)
        (internal if "stillrot.github.io" in full else external).append(row)
    out = []
    if internal:
        out.append("### Internal links")
        out += internal
    if external:
        out.append("\n### External links")
        out += external
    return "\n".join(out)


# ---------- structured data sections (from JSON, not from JS-rendered HTML) ----------

def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def fmt_publications():
    d = load("publications.json")
    j, c = d.get("journals", []), d.get("conferences", [])
    out = ["## Publications", ""]
    out.append("### Journals (%d)" % len(j))
    for p in sorted(j, key=lambda x: (x.get("year", 0)), reverse=True):
        line = '- %s. "%s." %s, %s' % (p["authors"], p["title"], p["venue"], p.get("year", ""))
        if p.get("category"):
            line += " [%s]" % p["category"]
        if p.get("note"):
            line += " (%s)" % p["note"]
        if p.get("link"):
            lk = p["link"]
            if lk.startswith("./"):
                lk = SITE + "/" + lk[2:]
            line += " — %s" % lk
        out.append(line)
    out.append("")
    out.append("### Conferences (%d)" % len(c))
    for p in sorted(c, key=lambda x: (x.get("year", 0)), reverse=True):
        line = '- %s. "%s." %s, %s' % (p["authors"], p["title"], p["venue"], p.get("year", ""))
        if p.get("note"):
            line += " (%s)" % p["note"]
        if p.get("link"):
            lk = p["link"]
            if lk.startswith("./"):
                lk = SITE + "/" + lk[2:]
            line += " — %s" % lk
        out.append(line)
    return "\n".join(out)


def fmt_patents():
    d = load("patents.json")
    g, a = d.get("granted", []), d.get("application", [])
    out = ["## Patents", "", "### Granted (%d)" % len(g)]
    for p in g:
        out.append("- [%s] %s — %s (%s). Granted %s. Application %s." % (
            p["country"], p["patent_no"], p["title"], p.get("title_en", ""),
            p.get("granted_date", ""), p.get("application_no", "")))
    out.append("")
    out.append("### Applications (%d)" % len(a))
    for p in a:
        no = p.get("application_no") or p.get("publication_no", "")
        extra = ""
        if p.get("publication_no"):
            extra = ", publication %s %s" % (p["publication_no"], p.get("published_date", ""))
        out.append("- [%s] %s (%s). Application %s%s." % (
            p["country"], p["title"], p.get("title_en", ""), no, extra))
    return "\n".join(out)


def fmt_news():
    items = load("news.json")
    out = ["## News (%d)" % len(items), ""]
    for n in sorted(items, key=lambda x: x.get("date", ""), reverse=True):
        link = n.get("link") or n.get("url") or ""
        title = n.get("title", "")
        if n.get("title_en"):
            title += " / " + n["title_en"]
        line = "- %s — %s" % (n.get("date", ""), title)
        if n.get("source"):
            line += " (%s)" % n["source"]
        if link:
            line += " — " + link
        out.append(line)
        if n.get("summary"):
            out.append("  - " + n["summary"])
    return "\n".join(out)


def fmt_papers():
    items = load("papers.json")
    out = ["## Research / Papers (%d)" % len(items), ""]
    for p in items:
        authors = p.get("authors", "")
        if isinstance(authors, list):
            authors = ", ".join(authors)
        venue = p.get("venue_short") or p.get("venue", "")
        line = '- "%s"' % p.get("title", "")
        if p.get("short_title"):
            line += " (%s)" % p["short_title"]
        if venue:
            line += " — %s" % venue
        if p.get("year"):
            line += ", %s" % p["year"]
        if p.get("note"):
            line += " (%s)" % p["note"]
        out.append(line)
        if authors:
            out.append("  - Authors: " + authors)
        for key in ("abstract", "summary", "tldr", "description"):
            if p.get(key):
                out.append("  - " + str(p[key]))
                break
    return "\n".join(out)


# --------------------------------- build ---------------------------------

def build():
    pages = [(d, u, t, desc, *extract_page(d)) for (d, u, t, desc) in PAGES]

    # ---- llms-full.txt ----
    full = []
    full.append("# Dongsik Yoon — AI Engineer · Portfolio (full content)")
    full.append("")
    full.append("> Complete plain-text content and structure of %s/ , provided for "
                "LLMs/agents because the live site renders parts of its content with "
                "JavaScript. Contains: site map, every page's text, all internal/external "
                "links, and the full publications/patents/news/research data." % SITE)
    full.append("")
    full.append("Source of truth: the repository at github.com/Stillrot/Stillrot.github.io . "
                "Regenerate with tools/generate_llms.py after any content change.")
    full.append("")

    full.append("## Site map")
    for (d, u, t, desc, text, links) in pages:
        full.append("- %s%s — %s: %s" % (SITE, u, t, desc))
    full.append("- %s/llms.txt — short index (this file's table of contents)" % SITE)
    full.append("")

    for (d, u, t, desc, text, links) in pages:
        full.append("\n" + "=" * 70)
        full.append("## Page: %s  (%s%s)" % (t, SITE, u))
        full.append("_%s_" % desc)
        full.append("")
        full.append(text if text else "(no extractable text)")
        lb = links_block(u, links)
        if lb:
            full.append("")
            full.append(lb)

    full.append("\n" + "=" * 70)
    full.append(fmt_publications())
    full.append("\n" + "=" * 70)
    full.append(fmt_patents())
    full.append("\n" + "=" * 70)
    full.append(fmt_news())
    full.append("\n" + "=" * 70)
    full.append(fmt_papers())
    full.append("")

    full_text = "\n".join(full).rstrip() + "\n"

    # ---- llms.txt (short index per the llms.txt convention) ----
    idx = []
    idx.append("# Dongsik Yoon — AI Engineer")
    idx.append("")
    idx.append("> Portfolio of Dongsik Yoon (윤동식), AI Engineer — AI-driven image/video "
               "processing. Publications, patents, and project case studies (HDC LABS: "
               "fire detection, elevator situation analysis, IP/research).")
    idx.append("")
    idx.append("## Pages")
    for (d, u, t, desc, text, links) in pages:
        idx.append("- [%s](%s%s): %s" % (t, SITE, u, desc))
    idx.append("")
    idx.append("## Full content")
    idx.append("- [llms-full.txt](%s/llms-full.txt): the entire site content + data in "
               "one plain-text file (best for feeding to an LLM)" % SITE)
    idx_text = "\n".join(idx).rstrip() + "\n"

    with open(os.path.join(ROOT, "llms-full.txt"), "w", encoding="utf-8") as f:
        f.write(full_text)
    with open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(idx_text)

    print("wrote llms.txt (%d bytes) and llms-full.txt (%d bytes)" % (
        len(idx_text.encode()), len(full_text.encode())))


if __name__ == "__main__":
    build()
