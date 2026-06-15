#!/usr/bin/env python3
"""
Prerender the home page's data sections (Publications / Patents / News /
Research) into index.html as STATIC HTML, so a plain fetch of the root URL
(LLMs, search crawlers — which don't run JavaScript) sees real content instead
of empty "Loading…" placeholders.

This is progressive enhancement, not cloaking: main.js re-renders the very same
sections on load (it sets `target.innerHTML = ''` first), so browser users see
the identical dynamic version — the static content is replaced instantly. Bots
and humans get the same information. The markup mirrors main.js + reuses the
same CSS classes, so there is no visual flash before JS runs.

Localized fields (patent / news titles) are rendered in the page's DEFAULT
language (Korean), matching what a first-time visitor sees. The full bilingual
data lives in llms-full.txt.

Re-run after editing data/*.json (then re-run generate_llms.py too):
    python3 tools/prerender_home.py
"""
import os
import re
import json
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def load(name):
    with open(os.path.join(ROOT, "data", name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def hl_authors(s):
    # Bold "Dongsik Yoon" (matches main.js highlightAuthors), after escaping.
    return re.sub(r"(Dongsik Yoon\*?)", r'<span class="me">\1</span>', esc(s))


LINK_TAG = {
    "arxiv": "arXiv", "ieee": "IEEE Xplore", "cvf_openaccess": "CVF", "acm": "ACM DL",
    "mlr": "PMLR", "project_page": "Project page", "code": "Code",
    "internal": "Details", "external": "Link",
}


def render_publications():
    d = load("publications")
    journals = sorted(d["journals"], key=lambda x: -x["idx"])
    confs = sorted(d["conferences"], key=lambda x: -x["idx"])

    def badge(p):
        if p.get("category") == "SCI-E":
            return '<span class="badge sci">SCI-E</span>'
        if p.get("note") == "Oral":
            return '<span class="badge oral">Oral</span>'
        if p.get("venue") == "Under review":
            return '<span class="badge review">Under review</span>'
        return ""

    def item(p):
        note_in_badge = p.get("note") == "Oral"
        year = ""
        if p.get("year"):
            year = ", %s" % p["year"]
            if p.get("month"):
                year += "." + str(p["month"]).zfill(2)
        tags = ""
        if p.get("note") and not note_in_badge:
            tags += '<span class="link-tag">%s</span>' % esc(p["note"])
        if p.get("link"):
            tags += '<span class="link-tag">%s</span>' % LINK_TAG.get(p.get("link_type"), "Link")
        inner = (
            '<span class="idx">[%s]</span> %s '
            '<span class="authors">%s</span>, '
            '<em class="title">%s</em>, '
            '<span class="venue">%s</span>%s %s'
        ) % (p["idx"], badge(p), hl_authors(p["authors"]), esc(p["title"]),
             esc(p["venue"]), year, tags)
        if p.get("link"):
            ext = bool(re.match(r"https?://", p["link"]))
            attr = ' target="_blank" rel="noopener"' if ext else ""
            return '<li class="has-link"><a class="pub-row" href="%s"%s>%s</a></li>' % (
                esc(p["link"]), attr, inner)
        return "<li>%s</li>" % inner

    out = ['<h3 class="sub-h">International Journal</h3><ul class="pub-list">']
    out += [item(j) for j in journals]
    out.append('</ul><h3 class="sub-h">International Conference</h3><ul class="pub-list">')
    out += [item(c) for c in confs]
    out.append("</ul>")
    return "".join(out)


def render_patents():
    d = load("patents")

    def table(rows, granted):
        if granted:
            head = "<tr><th>#</th><th>Title</th><th>Patent No.</th><th>Application No.</th><th>Granted</th></tr>"
        else:
            head = "<tr><th>#</th><th>Title</th><th>Application/Publication No.</th><th>Date</th></tr>"
        body = []
        for r in rows:
            title = esc(r.get("title"))  # KO default (matches pickLang default)
            if granted:
                body.append(
                    '<tr><td class="num">[%s]</td><td>%s</td>'
                    '<td class="num">%s %s</td><td class="num">%s</td>'
                    '<td class="num">%s</td></tr>' % (
                        r["idx"], title, esc(r["country"]), esc(r["patent_no"]),
                        esc(r["application_no"]), esc(r.get("granted_date", ""))))
            else:
                ident = r.get("application_no") or ("Ref. %s" % r.get("reference_no") if r.get("reference_no") else "Pending")
                if r.get("publication_no"):
                    num = "%s %s (Pub. %s)" % (esc(r["country"]), esc(ident), esc(r["publication_no"]))
                else:
                    num = "%s %s" % (esc(r["country"]), esc(ident))
                body.append(
                    '<tr><td class="num">[%s]</td><td>%s</td>'
                    '<td class="num">%s</td><td class="num">%s</td></tr>' % (
                        r["idx"], title, num, esc(r.get("published_date") or r.get("filed_date") or "-")))
        return '<table class="patent-table"><thead>%s</thead><tbody>%s</tbody></table>' % (
            head, "".join(body))

    return ('<h3 class="sub-h">Granted</h3>%s'
            '<h3 class="sub-h">Application</h3>%s') % (
        table(d["granted"], True), table(d["application"], False))


def render_news():
    items = load("news")
    cards = []
    for n in items:
        thumb = ('<img src="%s" alt="" loading="lazy">' % esc(n["thumbnail_external"])) if n.get("thumbnail_external") else ""
        cards.append(
            '<a class="news-card" href="%s" target="_blank" rel="noopener">'
            '<div class="thumb">%s</div>'
            '<div class="body"><div class="date">%s %s</div>'
            '<div class="title">%s</div><div class="summary">%s</div></div></a>' % (
                esc(n.get("link", "")), thumb, esc(n.get("date", "")),
                esc(n.get("source", "")), esc(n.get("title", "")), esc(n.get("summary", ""))))
    return '<div class="news-grid">%s</div>' % "".join(cards)


def render_research():
    papers = load("papers")
    cards = []
    for p in papers:
        ext = bool(p.get("external_url"))
        href = p.get("external_url") or ("./papers/%s/" % p["slug"])
        thumb = p.get("list_thumb") or p.get("thumbnail_external") or ""
        thumb_html = ('<img src="%s" alt="%s" loading="lazy">' % (
            esc(thumb), esc(p.get("short_title") or p.get("title")))) if thumb else '<span class="paper-card-placeholder">📄</span>'
        attr = ' target="_blank" rel="noopener"' if ext else ""
        note = ('<span class="venue-note">%s</span>' % esc(p["note"])) if p.get("note") else ""
        affil = ('<div class="paper-card-affiliation">%s</div>' % esc(p["affiliation"])) if p.get("affiliation") else ""
        authors = p.get("authors", "")
        if isinstance(authors, list):
            authors = ", ".join(authors)
        cards.append(
            '<a class="paper-card" href="%s"%s>'
            '<div class="paper-card-thumb">%s</div>'
            '<div class="paper-card-info">'
            '<div class="paper-card-venue"><span class="venue-pill">%s</span>%s</div>'
            '<div class="paper-card-title">%s</div>'
            '<div class="paper-card-authors">%s</div>%s</div></a>' % (
                esc(href), attr, thumb_html, esc(p.get("venue_short", "")), note,
                esc(p.get("title", "")), hl_authors(authors), affil))
    return '<div class="paper-card-grid">%s</div>' % "".join(cards)


def inject(htmltext, name, content):
    pat = re.compile(r"(<!--prerender:" + re.escape(name) + r"-->)(.*?)(<!--/prerender-->)", re.S)
    new, n = pat.subn(lambda m: m.group(1) + content + m.group(3), htmltext)
    if n == 0:
        raise SystemExit("prerender marker for '%s' not found in index.html" % name)
    return new


def main():
    with open(INDEX, encoding="utf-8") as f:
        h = f.read()
    h = inject(h, "publications", render_publications())
    h = inject(h, "patents", render_patents())
    h = inject(h, "news", render_news())
    h = inject(h, "research", render_research())
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(h)
    print("prerendered home data sections into index.html")


if __name__ == "__main__":
    main()
