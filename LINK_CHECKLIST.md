# Link checklist

Manual review aid that complements `scripts/check_links.py`.
The script auto-verifies the rows tagged `[auto]`; the others require human eyes.

## Internal navigation (auto)

- [x] `/` ↔ `news/`, `papers/`, `career/{hdclabs,metaent,ku,bu}/`
- [x] Every `papers/<slug>/index.html` links back to `papers/` and to root
- [x] Header nav on every page points to the same anchors and pages
- [x] `data/*.json` paths resolve (`papers.json`, `publications.json`, `patents.json`, `news.json`)

Run: `python3 scripts/check_links.py`

## External links (auto, opt-in)

Run: `python3 scripts/check_links.py --external`

Buckets to expect:

| Class             | Where used                                 | Notes                                                          |
| ----------------- | ------------------------------------------ | -------------------------------------------------------------- |
| `arxiv`           | publications, paper detail pages           | Should always return 200                                       |
| `ieee`            | paper detail pages                         | IEEE Xplore sometimes 403s on HEAD; script retries with GET    |
| `cvf_openaccess`  | ICCVW paper                                | 200                                                            |
| `acm`             | SIGGRAPH paper                             | 200                                                            |
| `mlr`             | ICLRW paper                                | 200                                                            |
| `code`            | BMVC paper                                 | GitHub repo                                                    |
| `project_page`    | ECCV (surfgan), NTU60-audio, KCI, Korea U  | github.io / webflow.io / pure.korea.ac.kr                      |
| `external`        | news (네이버, netmarble), socials, scholar | These are user-facing news clippings — open in a new tab       |

## Manual visual review

- [ ] Home page hero shows profile image and 3 social icons (GitHub, LinkedIn, Scholar)
- [ ] Career grid has 4 cards in this order: HDC LABS, Metaverse, Korea University, Baekseok University
- [ ] Publications list renders in **descending** index order, with the author "Dongsik Yoon" bolded
- [ ] Patents section shows two tables (Granted, Application) with correct counts (11 granted, 4 applications)
- [ ] News page shows 8 cards in reverse-chronological order
- [ ] Each paper detail page shows: title, venue line, authors (with bold), affiliation, link buttons, thumbnail+caption, abstract, ≥1 figure section, BibTeX
- [ ] BibTeX "Copy" button works in a browser (writes to clipboard)
- [ ] All career detail pages have at least one inline link back to a paper

## Known acceptable cases

- Some Webflow CDN thumbnails may 404 over time — the layout degrades gracefully (the surrounding `<figure>` still shows the caption).
- `cdn.prod.website-files.com` is a third-party CDN. If you want to fully self-host, run `scripts/check_links.py --external -v`, collect every `cdn.prod.website-files.com` URL, download to `assets/img/`, and rewrite the JSON `thumbnail_external` fields to point at the local copies (`./assets/img/...`).
