#!/usr/bin/env python3
"""Walk every HTML file under the site root, classify each link, and report broken / unreachable ones.

Usage:
    python3 scripts/check_links.py                 # internal links only (offline, fast)
    python3 scripts/check_links.py --external      # also HEAD-check every external URL
    python3 scripts/check_links.py --root .. -v    # custom root + verbose

Exit code 1 if any broken internal link is found.
External failures are reported but do not fail the build by default.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import html
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

HREF_RE = re.compile(r'href\s*=\s*"([^"]+)"', re.I)
SRC_RE = re.compile(r'src\s*=\s*"([^"]+)"', re.I)
# Preconnect / dns-prefetch links are just hostnames, not pages — skip.
PRECONNECT_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com", "cdn.prod.website-files.com"}

CLASSES = {
    "anchor": lambda h: h.startswith("#"),
    "mailto": lambda h: h.startswith("mailto:"),
    "tel": lambda h: h.startswith("tel:"),
    "arxiv": lambda h: urllib.parse.urlparse(h).netloc == "arxiv.org",
    "ieee": lambda h: urllib.parse.urlparse(h).netloc == "ieeexplore.ieee.org",
    "cvf_openaccess": lambda h: urllib.parse.urlparse(h).netloc == "openaccess.thecvf.com",
    "acm": lambda h: urllib.parse.urlparse(h).netloc == "dl.acm.org",
    "mlr": lambda h: urllib.parse.urlparse(h).netloc == "proceedings.mlr.press",
    "code": lambda h: urllib.parse.urlparse(h).netloc.endswith("github.com"),
    "project_page": lambda h: any(
        urllib.parse.urlparse(h).netloc.endswith(d)
        for d in (".github.io", ".webflow.io", "sites.google.com", "pure.korea.ac.kr",
                  "dcollection.korea.ac.kr", "kci.go.kr")
    ),
}


def classify(href: str) -> str:
    if href.startswith(("/", "./", "../")) or not urllib.parse.urlparse(href).scheme:
        return "internal"
    for name, fn in CLASSES.items():
        if fn(href):
            return name
    if urllib.parse.urlparse(href).scheme in ("http", "https"):
        return "external"
    return "other"


@dataclass
class Link:
    href: str
    source: str  # file where it was found
    kind: str
    target_file: str | None = None  # resolved internal target
    status: str = "?"  # "ok" / "missing" / "skipped" / "broken: 404" / etc.


@dataclass
class Report:
    by_kind: dict[str, list[Link]] = field(default_factory=lambda: defaultdict(list))
    broken: list[Link] = field(default_factory=list)

    def add(self, link: Link):
        self.by_kind[link.kind].append(link)
        if link.status not in ("ok", "skipped", "?"):
            self.broken.append(link)


def find_html_files(root: str) -> list[str]:
    out = []
    for dirpath, dirs, files in os.walk(root):
        # Skip hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "scripts", "site_crawl")]
        for f in files:
            if f.endswith(".html"):
                out.append(os.path.join(dirpath, f))
    return out


def extract_links(file_path: str) -> list[str]:
    with open(file_path, encoding="utf-8") as f:
        text = f.read()
    out = []
    for m in HREF_RE.finditer(text):
        href = html.unescape(m.group(1))
        # Skip <link rel="preconnect"> hostname-only entries
        host = urllib.parse.urlparse(href).netloc
        if host in PRECONNECT_HOSTS and not urllib.parse.urlparse(href).path.strip("/"):
            continue
        out.append(href)
    for m in SRC_RE.finditer(text):
        v = html.unescape(m.group(1))
        if not urllib.parse.urlparse(v).scheme:
            out.append(v)
    return out


def extract_json_urls(root: str) -> list[tuple[str, str]]:
    """Find every http(s) URL inside data/*.json and return (source, url) tuples."""
    import json
    data_dir = os.path.join(root, "data")
    out: list[tuple[str, str]] = []
    if not os.path.isdir(data_dir):
        return out
    for name in os.listdir(data_dir):
        if not name.endswith(".json"):
            continue
        path = os.path.join(data_dir, name)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        for url in re.findall(r'"(https?://[^"\s]+)"', text):
            out.append((os.path.relpath(path, root), url))
    return out


def resolve_internal(href: str, source_file: str, root: str) -> str | None:
    """Return absolute filesystem path the href should resolve to, or None if it cannot exist (anchor)."""
    # Strip fragment
    href_no_frag = href.split("#", 1)[0]
    if not href_no_frag:
        return None
    src_dir = os.path.dirname(source_file)
    if href_no_frag.startswith("/"):
        target = os.path.join(root, href_no_frag.lstrip("/"))
    else:
        target = os.path.normpath(os.path.join(src_dir, href_no_frag))
    # Directory link -> index.html
    if target.endswith("/") or os.path.isdir(target):
        target = os.path.join(target.rstrip("/"), "index.html")
    return target


UA = "Mozilla/5.0 (link-checker; +https://github.com/) compatible"


def head_check(url: str, timeout: int = 10) -> tuple[bool, str]:
    headers = {"User-Agent": UA, "Accept": "*/*"}
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=headers)
            if method == "GET":
                req.add_header("Range", "bytes=0-0")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status < 400, f"HTTP {resp.status} ({method})"
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 501):
                continue
            # Treat 999 (LinkedIn) and similar anti-bot codes as inconclusive, not broken
            if e.code in (429, 503, 999):
                return True, f"HTTP {e.code} (treated as ok)"
            return False, f"HTTP {e.code}"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"
    return False, "exhausted"


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   help="Site root (default: parent of scripts/)")
    p.add_argument("--external", action="store_true", help="HEAD-check external URLs as well")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(list(argv) if argv else None)

    root = os.path.abspath(args.root)
    print(f"site root: {root}")

    files = find_html_files(root)
    json_links = extract_json_urls(root)
    print(f"scanning {len(files)} html file(s) and {len(json_links)} URL(s) in data/*.json…")

    report = Report()
    for fp in files:
        for href in extract_links(fp):
            kind = classify(href)
            link = Link(href=href, source=os.path.relpath(fp, root), kind=kind)
            if kind == "anchor":
                link.status = "skipped"
            elif kind in ("mailto", "tel"):
                link.status = "skipped"
            elif kind == "internal":
                target = resolve_internal(href, fp, root)
                link.target_file = target
                if target is None or os.path.exists(target):
                    link.status = "ok"
                else:
                    link.status = f"missing: {os.path.relpath(target, root) if target else '?'}"
            else:
                link.status = "?" if not args.external else link.status
            report.add(link)

    # JSON-embedded URLs (the IEEE / arXiv / ACM links live in data/*.json, not HTML)
    for src, url in json_links:
        link = Link(href=url, source=src, kind=classify(url))
        if not args.external:
            link.status = "?"
        report.add(link)

    # External HEAD checks (in parallel)
    if args.external:
        unique = {}
        for kind, items in report.by_kind.items():
            if kind in ("internal", "anchor", "mailto", "tel"):
                continue
            for l in items:
                unique.setdefault(l.href, []).append(l)
        print(f"checking {len(unique)} unique external URL(s) (HEAD)…")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {pool.submit(head_check, url): url for url in unique}
            for fut in concurrent.futures.as_completed(futs):
                url = futs[fut]
                ok, msg = fut.result()
                for l in unique[url]:
                    l.status = "ok" if ok else f"broken: {msg}"
                    if not ok and l not in report.broken:
                        report.broken.append(l)

    # Summary
    print("\n=== Summary by link class ===")
    for kind in sorted(report.by_kind):
        items = report.by_kind[kind]
        ok = sum(1 for l in items if l.status == "ok")
        sk = sum(1 for l in items if l.status == "skipped")
        bad = sum(1 for l in items if l.status not in ("ok", "skipped", "?"))
        unk = sum(1 for l in items if l.status == "?")
        print(f"  {kind:<16}  total={len(items):<4}  ok={ok:<4}  broken={bad:<4}  skipped={sk:<4}  not-checked={unk}")

    if args.verbose:
        print("\n=== All links ===")
        for kind, items in report.by_kind.items():
            print(f"\n[{kind}]")
            for l in items:
                print(f"  {l.status:<24}  {l.source}  ->  {l.href}")

    if report.broken:
        print(f"\n!! {len(report.broken)} broken link(s):")
        for l in report.broken:
            print(f"  [{l.kind}] {l.source}  ->  {l.href}   ({l.status})")
        # Only fail on internal breakages by default
        if any(l.kind == "internal" for l in report.broken):
            return 1
    else:
        print("\nall good ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
