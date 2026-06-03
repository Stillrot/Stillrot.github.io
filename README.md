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
│   └── img/                # logos, profile + self-hosted figures (ext/)
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

The home page's data sections are **prerendered into `index.html`** (`tools/prerender_home.py`), so a no-JS / plain fetch still shows real content. Dynamic re-rendering and the other data-driven pages still use `fetch()`, so **serve over HTTP** for full functionality (file:// falls back to the static HTML).

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

## Self-hosted images & generated files

Project figures and thumbnails are **self-hosted** under `assets/img/ext/` — no
dependency on the Webflow CDN. (News-outlet, HuggingFace, arXiv, and YouTube
images are intentionally left external.) After adding any new
`cdn.prod.website-files.com` image, re-sync and refresh the generated files:

    python3 tools/self_host_images.py   # download new Webflow images + rewrite refs
    python3 tools/prerender_home.py     # refresh the home static fallback (raw-HTML content)
    python3 tools/generate_llms.py      # refresh llms.txt / llms-full.txt

`llms.txt` / `llms-full.txt` (repo root) give LLMs and agents the full site
content in plain text, since the live pages render some data with JavaScript.
