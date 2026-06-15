# Dongsik Yoon — Portfolio (static)

Personal portfolio — a hand-built static site on **GitHub Pages** with zero build step.

## Layout

```
portfolio/
├── index.html              # Home (profile, career grid, publications, patents)
├── news/index.html         # /news/
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
│   ├── hdclabs/index.html
│   ├── metaent/index.html
│   ├── ku/index.html
│   └── bu/index.html
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
├── tools/                  # generators: prerender_home.py, generate_llms.py
├── llms.txt                # short index for LLMs / agents
├── llms-full.txt           # full site content for LLMs / agents
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

## Images & generated files

Project figures and thumbnails are **self-hosted** under `assets/img/ext/` (no
external-CDN dependency for the core images). A few third-party images (news
outlets, HuggingFace, arXiv, YouTube) are linked externally on purpose.

After editing `data/*.json` or page content, refresh the generated files:

    python3 tools/prerender_home.py     # refresh the home static fallback (raw-HTML content)
    python3 tools/generate_llms.py      # refresh llms.txt / llms-full.txt
    python3 tools/generate_pdfs.py      # refresh assets/pdf + the 3 PDFs in ~/Downloads

PDF generation writes the canonical files to `assets/pdf/`, then mirrors only
these three files into the top-level Downloads folder:

    ~/Downloads/Dongsik_Yoon_Resume.pdf
    ~/Downloads/Dongsik_Yoon_CV.pdf
    ~/Downloads/Dongsik_Yoon_Portfolio.pdf

While editing the print pages, keep this watcher running in another terminal:

    python3 tools/watch_pdfs.py

`llms.txt` / `llms-full.txt` (repo root) give LLMs and agents the full site
content in plain text, since the live pages render some data with JavaScript.

A **git hook set** in `tools/hooks/` keeps generated and local PDF outputs in
sync. `pre-commit` runs the generators automatically on every commit and
re-stages the repo outputs, so they always match the committed content. The
post hooks (`post-commit`, `post-checkout`, `post-merge`, `post-rewrite`) mirror
the committed `assets/pdf/` files into `~/Downloads` after local Git changes
such as commits, branch switches, pulls, and rebases. Activate once per clone:

    git config core.hooksPath tools/hooks

The mirror hook refreshes only the three top-level
`~/Downloads/Dongsik_Yoon_*.pdf` files listed above.

To have Codex/local commits push themselves to GitHub after every successful
commit, opt in per clone:

    git config portfolio.autoPush true

The auto-push hook uses the normal Git credential setup for this Mac. It never
stores GitHub tokens in the repository. Disable it with:

    git config --unset portfolio.autoPush
