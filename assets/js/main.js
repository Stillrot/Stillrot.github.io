// Shared helpers across the static site.
// All data lives in /data/*.json, loaded relative to the page via `data-root` on <body>.

(function () {
  function root() {
    return document.body.dataset.root || './';
  }
  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') node.className = v;
      else if (k === 'dataset') Object.assign(node.dataset, v);
      else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2), v);
      else if (v != null && v !== false) node.setAttribute(k, v);
    }
    for (const c of children.flat()) {
      if (c == null) continue;
      node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }
    return node;
  }
  async function loadJSON(name) {
    const res = await fetch(`${root()}data/${name}.json`, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`failed to load ${name}.json: ${res.status}`);
    return res.json();
  }

  function highlightAuthors(authorsStr) {
    // Bold "Dongsik Yoon" wherever it appears.
    return authorsStr.replace(/(Dongsik Yoon\*?)/g, '<span class="me">$1</span>');
  }

  function venueBadge(item) {
    if (item.category === 'SCI-E') return '<span class="badge sci">SCI-E</span>';
    if (item.note === 'Oral') return '<span class="badge oral">Oral</span>';
    if (item.venue === 'Under review') return '<span class="badge review">Under review</span>';
    return '';
  }

  function linkTag(linkType) {
    const map = {
      arxiv: 'arXiv', ieee: 'IEEE Xplore', cvf_openaccess: 'CVF', acm: 'ACM DL',
      mlr: 'PMLR', project_page: 'Project page', code: 'Code', internal: 'Details', external: 'Link'
    };
    return map[linkType] || 'Link';
  }

  function renderPublications(target, data) {
    target.innerHTML = '';
    const journals = data.journals.slice().sort((a, b) => b.idx - a.idx);
    const conferences = data.conferences.slice().sort((a, b) => b.idx - a.idx);

    target.appendChild(el('h3', { class: 'sub-h' }, 'International Journal'));
    const ul1 = el('ul', { class: 'pub-list' });
    for (const j of journals) ul1.appendChild(renderPubItem(j));
    target.appendChild(ul1);

    target.appendChild(el('h3', { class: 'sub-h' }, 'International Conference'));
    const ul2 = el('ul', { class: 'pub-list' });
    for (const c of conferences) ul2.appendChild(renderPubItem(c));
    target.appendChild(ul2);
  }

  function renderPubItem(p) {
    const li = el('li', { class: p.link ? 'has-link' : '' });
    // If the front badge already shows the note (e.g. "Oral"), don't repeat it as a trailing tag.
    const noteInBadge = p.note === 'Oral';
    const inner = `
      <span class="idx">[${p.idx}]</span>
      ${venueBadge(p)}
      <span class="authors">${highlightAuthors(p.authors)}</span>,
      <em class="title">${escapeHtml(p.title)}</em>,
      <span class="venue">${escapeHtml(p.venue)}</span>${p.year ? `, ${p.year}${p.month ? '.' + String(p.month).padStart(2,'0') : ''}` : ''}
      ${p.note && !noteInBadge ? `<span class="link-tag">${escapeHtml(p.note)}</span>` : ''}
      ${p.link ? `<span class="link-tag">${linkTag(p.link_type)}</span>` : ''}
    `;
    if (p.link) {
      const isExternal = /^https?:\/\//.test(p.link);
      const a = el('a', {
        class: 'pub-row',
        href: p.link,
        ...(isExternal ? { target: '_blank', rel: 'noopener' } : {}),
      });
      a.innerHTML = inner;
      li.appendChild(a);
    } else {
      li.innerHTML = inner;
    }
    return li;
  }

  function renderPatents(target, data) {
    target.innerHTML = '';
    target.appendChild(el('h3', { class: 'sub-h' }, 'Granted'));
    target.appendChild(renderPatentTable(data.granted, true));
    target.appendChild(el('h3', { class: 'sub-h' }, 'Application'));
    target.appendChild(renderPatentTable(data.application, false));
  }

  function renderPatentTable(rows, granted) {
    const table = el('table', { class: 'patent-table' });
    const head = el('thead');
    head.innerHTML = granted
      ? '<tr><th>#</th><th>Title</th><th>Patent No.</th><th>Application No.</th><th>Granted</th></tr>'
      : '<tr><th>#</th><th>Title</th><th>Application/Publication No.</th><th>Date</th></tr>';
    table.appendChild(head);
    const body = el('tbody');
    rows.forEach((r) => {
      const tr = el('tr');
      if (granted) {
        tr.innerHTML = `
          <td class="num">[${r.idx}]</td>
          <td>${escapeHtml(r.title)}</td>
          <td class="num">${escapeHtml(r.country)} ${escapeHtml(r.patent_no)}</td>
          <td class="num">${escapeHtml(r.application_no)}</td>
          <td class="num">${escapeHtml(r.granted_date)}</td>`;
      } else {
        const num = r.publication_no
          ? `${escapeHtml(r.country)} ${escapeHtml(r.application_no)} (Pub. ${escapeHtml(r.publication_no)})`
          : `${escapeHtml(r.country)} ${escapeHtml(r.application_no)}`;
        tr.innerHTML = `
          <td class="num">[${r.idx}]</td>
          <td>${escapeHtml(r.title)}</td>
          <td class="num">${num}</td>
          <td class="num">${escapeHtml(r.published_date || '-')}</td>`;
      }
      body.appendChild(tr);
    });
    table.appendChild(body);
    return table;
  }

  function renderNews(target, items) {
    target.innerHTML = '';
    const grid = el('div', { class: 'news-grid' });
    items.forEach((n) => {
      const a = el('a', { class: 'news-card', href: n.link, target: '_blank', rel: 'noopener' });
      a.innerHTML = `
        <div class="thumb">${n.thumbnail_external ? `<img src="${n.thumbnail_external}" alt="" loading="lazy">` : ''}</div>
        <div class="body">
          <div class="date">${escapeHtml(n.date)} · ${escapeHtml(n.source || '')}</div>
          <div class="title">${escapeHtml(n.title)}</div>
          <div class="summary">${escapeHtml(n.summary)}</div>
        </div>`;
      grid.appendChild(a);
    });
    target.appendChild(grid);
  }

  function renderPaper(target, paper) {
    document.title = `${paper.short_title || paper.title} · Dongsik Yoon`;
    const sectionsHtml = (paper.sections || [])
      .map((sec) => {
        const isRow = sec.layout === 'row';
        const figs = (sec.figures || [])
          .map(
            (f) => isRow
              ? `
              <figure class="row-figure">
                <img src="${f.src}" alt="${escapeHtml(f.caption || sec.title)}" loading="lazy">
                ${f.caption ? `<figcaption>${escapeHtml(f.caption)}</figcaption>` : ''}
              </figure>`
              : `
              <figure class="paper-figure">
                <img src="${f.src}" alt="${escapeHtml(f.caption || sec.title)}" loading="lazy">
                ${f.caption ? `<figcaption>${escapeHtml(f.caption)}</figcaption>` : ''}
              </figure>`
          )
          .join('');
        const bullets = (sec.bullets || [])
          .map((b) => `<li>${escapeHtml(b)}</li>`)
          .join('');
        return `
        <h2>${escapeHtml(sec.title)}</h2>
        ${sec.intro ? `<p>${escapeHtml(sec.intro)}</p>` : ''}
        ${bullets ? `<ul>${bullets}</ul>` : ''}
        ${isRow ? `<div class="row-figure-grid" data-cols="${sec.figures.length}">${figs}</div>` : figs}
        ${sec.intro_after ? `<p class="figure-caption-after">${escapeHtml(sec.intro_after)}</p>` : ''}`;
      })
      .join('');

    target.innerHTML = `
      <section class="paper-header">
        <div class="container">
          <h1>${escapeHtml(paper.title)}</h1>
          <div class="venue-line"><strong>${escapeHtml(paper.venue)}</strong>${paper.year ? `, ${paper.year}` : ''}${paper.note ? ` · <span class="venue-note">${escapeHtml(paper.note)}</span>` : ''}</div>
          <div class="authors">${highlightAuthors(paper.authors.join(', '))}</div>
          <div class="affiliation">${escapeHtml(paper.affiliation || '')}</div>
          <div class="link-row">
            ${paper.links.map((l) => `<a class="btn-link" data-type="${l.type}" href="${l.url}" target="_blank" rel="noopener">${escapeHtml(l.label)}</a>`).join('')}
          </div>
        </div>
      </section>

      <section class="container">
        ${paper.thumbnail_external ? `
        <h2 class="paper-section-heading">Overview</h2>
        <figure class="paper-thumb">
          <img src="${paper.thumbnail_external}" alt="${escapeHtml(paper.short_title || paper.title)}" loading="lazy">
          ${paper.thumbnail_caption ? `<figcaption>${escapeHtml(paper.thumbnail_caption)}</figcaption>` : ''}
        </figure>` : ''}

        ${paper.video_id ? `
        <h2 class="paper-section-heading">${escapeHtml(paper.video_heading || 'Presentation')}</h2>
        <div class="paper-video">
          <iframe src="https://www.youtube.com/embed/${encodeURIComponent(paper.video_id)}?rel=0&controls=1"
                  frameborder="0"
                  allow="autoplay; encrypted-media"
                  allowfullscreen
                  title="${escapeHtml(paper.video_title || paper.short_title || paper.title)}"></iframe>
        </div>` : ''}

        <div class="paper-body">
          <h2>Abstract</h2>
          <p>${escapeHtml(paper.abstract)}</p>

          ${sectionsHtml}

          <h2>BibTeX</h2>
          <div class="bibtex-box">
            <button class="copy" type="button">Copy</button>
            <pre id="bibtex-pre">${escapeHtml(paper.bibtex)}</pre>
          </div>
        </div>
      </section>`;
    const copyBtn = target.querySelector('.bibtex-box .copy');
    if (copyBtn) {
      copyBtn.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(paper.bibtex);
          copyBtn.textContent = 'Copied!';
          setTimeout(() => (copyBtn.textContent = 'Copy'), 1500);
        } catch (e) {
          copyBtn.textContent = 'Copy failed';
        }
      });
    }
  }

  function renderPaperList(target, papers) {
    target.innerHTML = '';
    const grid = el('div', { class: 'paper-card-grid' });
    // Use the order as it appears in papers.json (curator-controlled).
    papers.forEach((p) => {
      const isExternal = !!p.external_url;
      const href = p.external_url || `./${p.slug}/`;
      const thumb = p.list_thumb || p.thumbnail_external || '';
      const a = el('a', {
        class: 'paper-card',
        href,
        ...(isExternal ? { target: '_blank', rel: 'noopener' } : {}),
      });
      a.innerHTML = `
        <div class="paper-card-thumb">
          ${thumb ? `<img src="${thumb}" alt="${escapeHtml(p.short_title || p.title)}" loading="lazy">` : '<span class="paper-card-placeholder">📄</span>'}
        </div>
        <div class="paper-card-info">
          <div class="paper-card-venue">
            <span class="venue-pill">${escapeHtml(p.venue_short)}</span>
            ${p.note ? `<span class="venue-note">${escapeHtml(p.note)}</span>` : ''}
          </div>
          <div class="paper-card-title">${escapeHtml(p.title)}</div>
          <div class="paper-card-authors">${highlightAuthors(p.authors.join(', '))}</div>
          ${p.affiliation ? `<div class="paper-card-affiliation">${escapeHtml(p.affiliation)}</div>` : ''}
        </div>`;
      grid.appendChild(a);
    });
    target.appendChild(grid);
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // Highlights the matching nav link as the user scrolls past each section.
  // Simple approach: pick whichever section's top is closest to (and above) the
  // sticky header bottom. Works whether the user scrolls or clicks an anchor.
  function initScrollSpy() {
    const sectionIds = ['hero', 'career', 'publications'];
    const sections = sectionIds
      .map((id) => document.getElementById(id))
      .filter(Boolean);
    if (!sections.length) return;
    const navLinks = [...document.querySelectorAll('nav.primary a')];

    function activate(id) {
      navLinks.forEach((a) => {
        const h = a.getAttribute('href');
        const matches =
          (id === 'hero' && (h === './' || h === '/' || h === '#')) ||
          (id !== 'hero' && h === '#' + id);
        a.classList.toggle('active', matches);
      });
    }

    function update() {
      const offset = 90;  // a bit past the sticky header
      let current = sections[0];
      for (const s of sections) {
        if (s.getBoundingClientRect().top - offset <= 0) current = s;
      }
      activate(current.id);
    }

    let raf = null;
    window.addEventListener('scroll', () => {
      if (raf) return;
      raf = requestAnimationFrame(() => { raf = null; update(); });
    }, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  // Page bootstraps
  async function bootHome() {
    const pubBox = document.getElementById('publications-root');
    const patBox = document.getElementById('patents-root');
    try {
      const [pubs, pats] = await Promise.all([loadJSON('publications'), loadJSON('patents')]);
      if (pubBox) renderPublications(pubBox, pubs);
      if (patBox) renderPatents(patBox, pats);
    } catch (e) {
      console.error(e);
      if (pubBox) pubBox.textContent = '데이터를 불러오지 못했습니다.';
    }
    // Data is async — once it lands, the page layout shifts. If the URL had a hash,
    // re-anchor so the user lands at the right place (not where the empty placeholder was).
    if (window.location.hash) {
      const id = decodeURIComponent(window.location.hash.slice(1));
      const target = document.getElementById(id);
      if (target) target.scrollIntoView({ block: 'start' });
    }
    initScrollSpy();
  }
  async function bootNews() {
    const box = document.getElementById('news-root');
    if (!box) return;
    try {
      const items = await loadJSON('news');
      renderNews(box, items);
    } catch (e) { box.textContent = '데이터를 불러오지 못했습니다.'; }
  }
  async function bootPaperList() {
    const box = document.getElementById('paper-list-root');
    if (!box) return;
    try {
      const papers = await loadJSON('papers');
      renderPaperList(box, papers);
    } catch (e) { box.textContent = '데이터를 불러오지 못했습니다.'; }
  }
  async function bootPaper() {
    const box = document.getElementById('paper-root');
    if (!box) return;
    const slug = box.dataset.slug;
    try {
      const papers = await loadJSON('papers');
      const p = papers.find((x) => x.slug === slug);
      if (!p) { box.textContent = `Paper "${slug}" not found.`; return; }
      renderPaper(box, p);
    } catch (e) { box.textContent = '데이터를 불러오지 못했습니다.'; }
  }

  window.Portfolio = { bootHome, bootNews, bootPaperList, bootPaper };
})();
