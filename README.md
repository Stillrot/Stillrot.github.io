# Dongsik Yoon · Portfolio (static)

Static mirror of [dongsik-yoon.webflow.io](https://dongsik-yoon.webflow.io/) that runs on **GitHub Pages** with zero build step.

## Layout

```
portfolio/
├── index.html              # Home (profile, career grid, publications, patents)
├── news/index.html         # /news/  ← original /news-ds
├── papers/
│   ├── index.html          # paper listing
│   ├── wacvw2026/index.html
│   ├── iccvw2025/index.html
│   ├── iclrw2025/index.html
│   ├── siggraph2024/index.html
│   ├── access2023/index.html
│   ├── grsl2023/index.html
│   ├── icip2022/index.html
│   └── bmvc2021/index.html
├── career/
│   ├── hdclabs/index.html  # ← /hdclabs
│   ├── metaent/index.html  # ← /metaent
│   ├── ku/index.html       # ← /ku
│   └── bu/index.html       # ← /bu
├── data/
│   ├── papers.json         # title, authors, venue, abstract, figures, bibtex …
│   ├── publications.json   # journals + conferences
│   ├── patents.json        # granted + applications
│   └── news.json           # press clippings
├── assets/
│   ├── css/style.css
│   ├── js/main.js          # shared renderers: bootHome / bootNews / bootPaperList / bootPaper
│   └── img/                # (empty — see "Self-host images" below)
├── scripts/
│   └── check_links.py
├── sitemap.xml
├── SITEMAP.md
├── LINK_CHECKLIST.md
└── README.md
```

`SITEMAP.md` explains the URL → file mapping and the link-classification rules.

## Local preview

```bash
cd portfolio
python3 -m http.server 8123
# open http://localhost:8123/
```

The data is fetched at runtime via `fetch()`, so **you must serve over HTTP** (file:// won't work).

## Deploy to GitHub Pages

1. Push the `portfolio/` directory to a GitHub repo. The page root is wherever you choose — every `<a href>` and `<script src>` in this project is **relative**, so it works at:
   * `https://<user>.github.io/` (user/org page)
   * `https://<user>.github.io/<repo>/` (project page)
2. In the repo settings → Pages, pick the branch and the `/portfolio` (or `/`) folder.

No CI required. Push → deploy.

## Editing content

| Goal                                | Edit                                              |
| ----------------------------------- | ------------------------------------------------- |
| Add a new paper detail page         | Add a row to `data/papers.json`, then create `papers/<slug>/index.html` from any sibling as a template (only the `data-slug` differs) |
| Add a publication to the home list  | Append to `data/publications.json` (`journals` or `conferences`) |
| Add a patent                        | Append to `data/patents.json` (`granted` or `application`) |
| Add a news item                     | Prepend to `data/news.json`                       |
| Update a career page                | Edit the HTML in `career/<slug>/index.html`       |
| Change colors / typography          | Edit the CSS variables at the top of `assets/css/style.css` |

## Link checker

```bash
# Internal links only (fast, offline). Exit code 1 if any internal link is broken.
python3 scripts/check_links.py

# Also HEAD-check every external URL in parallel
python3 scripts/check_links.py --external

# Verbose log of every (file → href → status)
python3 scripts/check_links.py --external -v
```

Output is grouped by link class — `internal`, `anchor`, `arxiv`, `ieee`, `cvf_openaccess`, `acm`, `mlr`, `code`, `project_page`, `external` — so you can confirm at a glance that each kind has the expected count.

See `LINK_CHECKLIST.md` for the manual review steps.

## Self-host images (optional)

By default thumbnails are loaded from `cdn.prod.website-files.com` (the original Webflow CDN). To make the site fully self-contained:

1. `python3 scripts/check_links.py --external -v | grep cdn.prod.website-files.com`
2. Download each URL into `assets/img/`.
3. In `data/papers.json` and `data/news.json`, replace `thumbnail_external` with `./assets/img/<filename>` (or `../../assets/img/<filename>` for paper detail pages — `main.js` already uses relative paths via `data-root`).
