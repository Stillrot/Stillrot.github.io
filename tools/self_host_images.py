#!/usr/bin/env python3
"""
Download Webflow-CDN images into assets/img/ext/ and rewrite papers.json,
news.json, and career/*/index.html to point at the local copies — so the site
no longer depends on cdn.prod.website-files.com (which can 404 over time and
leave broken images / caption-only layouts).

Scope: ONLY cdn.prod.website-files.com (the user's own Webflow uploads). Left as
external on purpose:
  - imgnews.pstatic.net  (news-outlet photos — third-party copyright)
  - huggingface.co / arxiv.org / img.youtube.com (stable, third-party hosts)

Path conventions after rewrite:
  - JSON (shared by '/' and '/papers/<slug>/') -> root-absolute  /assets/img/ext/NAME
  - career HTML (always at /career/<x>/)        -> relative      ../../assets/img/ext/NAME

Idempotent: re-running after a successful pass finds no Webflow URLs and is a
no-op; downloads are skipped if the file already exists.

Run, then refresh derived files:
    python3 tools/self_host_images.py
    python3 tools/prerender_home.py && python3 tools/generate_llms.py
"""
import os
import re
import glob
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTDIR = os.path.join(ROOT, "assets", "img", "ext")
URLRE = re.compile(r"https://cdn\.prod\.website-files\.com/[^\"'\s<>)]+")

JSON_FILES = ["data/papers.json", "data/news.json"]
HTML_FILES = sorted(glob.glob(os.path.join(ROOT, "career", "*", "index.html")))


def local_name(url):
    return url.split("?")[0].rstrip("/").split("/")[-1]


def collect_urls():
    urls = set()
    for rel in JSON_FILES:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            urls |= set(URLRE.findall(f.read()))
    for f in HTML_FILES:
        with open(f, encoding="utf-8") as fh:
            urls |= set(URLRE.findall(fh.read()))
    return sorted(urls)


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return "cached"
    r = subprocess.run(
        ["curl", "-sS", "-L", "--max-time", "45", "-o", dest, url],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if r.returncode != 0 or (not os.path.exists(dest)) or os.path.getsize(dest) == 0:
        if os.path.exists(dest):
            os.remove(dest)
        return "FAILED"
    return "ok"


def rewrite(path, mapping, prefix):
    with open(path, encoding="utf-8") as f:
        t = f.read()
    n = 0
    for url, name in mapping.items():
        new = prefix + name
        if url in t:
            t = t.replace(url, new)
            n += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(t)
    return n


def main():
    os.makedirs(DESTDIR, exist_ok=True)
    urls = collect_urls()
    print("%d unique Webflow URL(s) found" % len(urls))
    if not urls:
        print("nothing to do (already self-hosted)")
        return
    mapping, failed = {}, []
    for u in urls:
        name = local_name(u)
        status = download(u, os.path.join(DESTDIR, name))
        print("  [%-6s] %s" % (status, name))
        if status in ("ok", "cached"):
            mapping[u] = name
        else:
            failed.append(u)
    if failed:
        print("\n!! %d download(s) FAILED — leaving those URLs untouched:" % len(failed))
        for u in failed:
            print("   ", u)
    # rewrite references
    for rel in JSON_FILES:
        c = rewrite(os.path.join(ROOT, rel), mapping, "/assets/img/ext/")
        print("rewrote %d url(s) in %s" % (c, rel))
    for f in HTML_FILES:
        c = rewrite(f, mapping, "../../assets/img/ext/")
        print("rewrote %d url(s) in %s" % (c, os.path.relpath(f, ROOT)))
    print("\ndone — %d image(s) now self-hosted under assets/img/ext/" % len(mapping))


if __name__ == "__main__":
    main()
