# Sitemap

Dongsik Yoon portfolio — static site (GitHub Pages).
All paths are relative to the site root (`/`) so the deploy works at any GitHub Pages base path.

## Pages

| Path | Purpose |
| ---- | ------- |
| `/` | Home: profile, career list, publications, patents |
| `/news/` | Press/news clippings |
| `/career/hdclabs/` | HDC LABS career detail |
| `/career/metaent/` | Metaverse Entertainment career detail |
| `/career/ku/` | Korea University M.S. career detail |
| `/career/bu/` | Baekseok University B.S. career detail |
| `/papers/` | Listing of paper detail pages |
| `/papers/wacvw2026/` | WACVW 2026 paper |
| `/papers/iccvw2025/` | ICCVW 2025 paper |
| `/papers/iclrw2025/` | ICLRW 2025 paper |
| `/papers/siggraph2024/` | SIGGRAPH Asia 2024 poster |
| `/papers/access2023/` | IEEE Access 2023 paper |
| `/papers/grsl2023/` | IEEE GRSL 2023 paper |
| `/papers/icip2022/` | IEEE ICIP 2022 paper |
| `/papers/bmvc2021/` | BMVC 2021 paper |

## Data files (JSON)

| File | Loaded by | Schema |
| ---- | --------- | ------ |
| `data/papers.json` | `/papers/`, paper detail pages | `[{slug, title, venue, year, authors, abstract, links, bibtex, thumbnail, affiliation}]` |
| `data/publications.json` | `/` | `{journals:[...], conferences:[...]}` with `{idx, title, authors, venue, year, link, link_type, note}` per entry |
| `data/patents.json` | `/` | `{granted:[...], application:[...]}` |
| `data/news.json` | `/news/` | `[{date, title, summary, link, thumbnail}]` |

## Link classification rules (used by `scripts/check_links.py`)

| Class | Detected by |
| ----- | ----------- |
| `internal` | href starts with `/`, `./`, or `../`, and resolves to a file inside the site |
| `anchor` | href starts with `#` |
| `arxiv` | host equals `arxiv.org` |
| `ieee` | host equals `ieeexplore.ieee.org` |
| `cvf_openaccess` | host equals `openaccess.thecvf.com` |
| `acm` | host equals `dl.acm.org` |
| `mlr` | host equals `proceedings.mlr.press` |
| `project_page` | github.io / similar — paper project pages |
| `code` | host equals `github.com` (non-pages) |
| `external` | anything else (news, social, scholar) |

## Build / deploy notes

* Pure static HTML/CSS/JS. No build step.
* All in-site hrefs use *relative* paths (`./papers/wacvw2026/`, `../../`, etc.) so the bundle works under `https://<user>.github.io/<repo>/`.
* JSON files are fetched at runtime via `fetch()` so the data can be edited without touching templates.
* `scripts/check_links.py` walks every emitted HTML and verifies all internal links resolve to a file on disk, then optionally HEAD-checks external links.
