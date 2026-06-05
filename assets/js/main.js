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
      const title = pickLang(r, 'title');
      if (granted) {
        tr.innerHTML = `
          <td class="num">[${r.idx}]</td>
          <td>${escapeHtml(title)}</td>
          <td class="num">${escapeHtml(r.country)} ${escapeHtml(r.patent_no)}</td>
          <td class="num">${escapeHtml(r.application_no)}</td>
          <td class="num">${escapeHtml(r.granted_date)}</td>`;
      } else {
        const num = r.publication_no
          ? `${escapeHtml(r.country)} ${escapeHtml(r.application_no)} (Pub. ${escapeHtml(r.publication_no)})`
          : `${escapeHtml(r.country)} ${escapeHtml(r.application_no)}`;
        tr.innerHTML = `
          <td class="num">[${r.idx}]</td>
          <td>${escapeHtml(title)}</td>
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
      const title = pickLang(n, 'title');
      const summary = pickLang(n, 'summary');
      const source = pickLang(n, 'source');
      a.innerHTML = `
        <div class="thumb">${n.thumbnail_external ? `<img src="${n.thumbnail_external}" alt="" loading="lazy">` : ''}</div>
        <div class="body">
          <div class="date">${escapeHtml(n.date)} ${escapeHtml(source || '')}</div>
          <div class="title">${escapeHtml(title)}</div>
          <div class="summary">${escapeHtml(summary)}</div>
        </div>`;
      grid.appendChild(a);
    });
    target.appendChild(grid);
  }

  function renderPaper(target, paper) {
    document.title = `${paper.short_title || paper.title} Dongsik Yoon`;
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
          <div class="venue-line"><strong>${escapeHtml(paper.venue)}</strong>${paper.year ? `, ${paper.year}` : ''}${paper.note ? ` <span class="venue-note">${escapeHtml(paper.note)}</span>` : ''}</div>
          <div class="authors">${highlightAuthors(paper.authors.join(', '))}</div>
          <div class="affiliation">${escapeHtml(paper.affiliation || '')}</div>
          <div class="link-row">
            ${paper.links.map((l) => `<a class="btn-link" data-type="${l.type}" href="${l.url}" target="_blank" rel="noopener">${escapeHtml(l.label)}</a>`).join('')}
          </div>
        </div>
      </section>

      <section class="container">
        ${paper.thumbnail_external ? `
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
      // Build href via data-root so the same renderer works from / (home tab) and /papers/.
      const href = p.external_url || `${root()}papers/${p.slug}/`;
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

  // Language toggle (KR / EN) — controls visibility of .ko-only / .en-only blocks
  // across every page. Persists choice in localStorage.
  function initLanguageToggle() {
    function set(lang) {
      document.documentElement.classList.remove('lang-ko', 'lang-en');
      document.documentElement.classList.add('lang-' + lang);
      document.documentElement.lang = lang;
      try { localStorage.setItem('siteLang', lang); } catch (e) {}
      document.querySelectorAll('.lang-toggle button').forEach((b) => {
        b.classList.toggle('active', b.dataset.lang === lang);
      });
      // Re-render data-driven views so they pick the right localized fields.
      if (window.__rerenderForLang) window.__rerenderForLang(lang);
    }
    let initial = 'ko';
    try { initial = localStorage.getItem('siteLang') || 'ko'; } catch (e) {}
    set(initial);
    document.querySelectorAll('.lang-toggle button').forEach((b) => {
      b.addEventListener('click', () => set(b.dataset.lang));
    });
  }

  function currentLang() {
    return document.documentElement.classList.contains('lang-en') ? 'en' : 'ko';
  }

  // Pick the localized field of a JSON object: prefer `<field>_<lang>`, fall back to `<field>`.
  function pickLang(obj, field) {
    const lang = currentLang();
    return obj[`${field}_${lang}`] || obj[field] || '';
  }

  // Highlights the matching nav link as the user scrolls past each section.
  // Simple approach: pick whichever section's top is closest to (and above) the
  // sticky header bottom. Works whether the user scrolls or clicks an anchor.
  function initScrollSpy() {
    // hero / career are scroll-spied; #content (the tabbed area) reflects whichever tab is active.
    const sectionIds = ['hero', 'career', 'content'];
    const sections = sectionIds
      .map((id) => document.getElementById(id))
      .filter(Boolean);
    if (!sections.length) return;
    const navLinks = [...document.querySelectorAll('nav.primary a')];

    function activate(id) {
      // If we're in the tabbed content section, mirror the active tab onto the nav.
      const activeTab = document.querySelector('.tab-btn.active')?.dataset.tab;
      const navTarget = id === 'content' && activeTab ? activeTab : id;
      navLinks.forEach((a) => {
        const h = a.getAttribute('href');
        const matches =
          (navTarget === 'hero' && (h === './' || h === '/' || h === '#')) ||
          (navTarget !== 'hero' && h === '#' + navTarget);
        a.classList.toggle('active', matches);
      });
    }

    function update() {
      const offset = 90;
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
    // When the active tab changes (tab click, top-nav link, or deep-link hash),
    // mirror it onto the nav right away instead of waiting for a scroll to land
    // on #content — otherwise the nav stays stuck on the section above it.
    document.addEventListener('tabchange', () => activate('content'));
    update();
  }

  // A fixed "documents" rail (Portfolio / CV / Resume) that follows on scroll.
  // Shown on the home page and the career detail pages; built in JS so the
  // markup lives in one place and links resolve via the page's data-root.
  function initDocRail() {
    const isHome = !!document.getElementById('hero');
    const isCareer = location.pathname.includes('/career/');
    if (!isHome && !isCareer) return;
    if (document.querySelector('.doc-rail')) return; // guard against double-init
    const root = document.body.getAttribute('data-root') || './';
    const ICONS = {
      portfolio: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 4h18a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zm1 2v12h16V6H4z"/><path d="M6 8h12v1.5H6zm0 3.5h9V13H6zm0 3.5h7V16.5H6z"/></svg>',
      cv: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 7V3.5L18.5 9H13zM8 13h8v1.5H8zm0 3h8v1.5H8zm0 3h5v1.5H8z"/></svg>',
      resume: '<svg viewBox="0 0 24 24" fill="currentColor" fill-rule="evenodd" aria-hidden="true"><path d="M5 2h14a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1zm3 4v2h8V6H8zm0 4v1.5h8V10H8zm0 3.5V15h8v-1.5H8zm0 3.5V18h5v-1.5H8z"/></svg>',
    };
    const rail = document.createElement('aside');
    rail.className = 'doc-rail';
    rail.setAttribute('aria-label', 'Documents');
    rail.innerHTML =
      '<a href="' + root + 'portfolio2026/" target="_blank" rel="noopener" title="Portfolio (Deck)">' + ICONS.portfolio + '<span class="dr-label">Portfolio</span></a>' +
      '<a href="' + root + 'cv/" title="CV">' + ICONS.cv + '<span class="dr-label">CV</span></a>' +
      '<a href="' + root + 'resume/" title="Resume">' + ICONS.resume + '<span class="dr-label">Resume</span></a>';
    document.body.appendChild(rail);

    const hero = document.getElementById('hero');
    let raf = null;
    function update() {
      // Home: appear once the hero is scrolled past (its docs are up there too).
      // Career: no hero, so appear after a small scroll.
      const show = hero ? hero.getBoundingClientRect().bottom < 120 : window.scrollY > 80;
      rail.classList.toggle('show', show);
    }
    window.addEventListener('scroll', () => {
      if (raf) return;
      raf = requestAnimationFrame(() => { raf = null; update(); });
    }, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  // Page bootstraps
  const TAB_NAMES = ['publications', 'patents', 'news', 'research'];

  function activateTab(name) {
    if (!TAB_NAMES.includes(name)) return;
    document.querySelectorAll('.tab-btn').forEach((b) => {
      const on = b.dataset.tab === name;
      b.classList.toggle('active', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    document.querySelectorAll('.tab-panel').forEach((p) => {
      p.classList.toggle('active', p.dataset.panel === name);
    });
    // Notify the scroll-spy so it can mirror this tab onto the top nav,
    // independent of the current scroll position.
    document.dispatchEvent(new CustomEvent('tabchange', { detail: name }));
  }

  function initTabs() {
    const buttons = document.querySelectorAll('.tab-btn');
    if (!buttons.length) return;
    buttons.forEach((b) => {
      b.addEventListener('click', () => {
        const name = b.dataset.tab;
        activateTab(name);
        // Update URL hash without triggering scroll
        history.replaceState(null, '', `#${name}`);
      });
    });
    // Initial activation from URL hash
    const initialHash = decodeURIComponent(location.hash.slice(1));
    if (TAB_NAMES.includes(initialHash)) activateTab(initialHash);
    // Sync on later hash changes (e.g. user clicks a nav link)
    window.addEventListener('hashchange', () => {
      const h = decodeURIComponent(location.hash.slice(1));
      if (TAB_NAMES.includes(h)) {
        activateTab(h);
        document.getElementById('content')?.scrollIntoView({ block: 'start' });
      }
    });
  }

  async function bootHome() {
    const pubBox = document.getElementById('publications-root');
    const patBox = document.getElementById('patents-root');
    const newsBox = document.getElementById('news-root');
    const paperBox = document.getElementById('paper-list-root');
    try {
      const [pubs, pats, news, papers] = await Promise.all([
        loadJSON('publications'),
        loadJSON('patents'),
        loadJSON('news'),
        loadJSON('papers'),
      ]);
      if (pubBox) renderPublications(pubBox, pubs);
      if (patBox) renderPatents(patBox, pats);
      if (newsBox) renderNews(newsBox, news);
      if (paperBox) renderPaperList(paperBox, papers);
    } catch (e) {
      // The home sections are prerendered into index.html (tools/prerender_home.py),
      // so on a fetch failure we keep that static fallback instead of blanking it.
      console.error(e);
    }
    initTabs();
    // After async render, re-anchor + activate tab if URL had hash
    if (window.location.hash) {
      const id = decodeURIComponent(window.location.hash.slice(1));
      if (TAB_NAMES.includes(id)) {
        activateTab(id);
        document.getElementById('content')?.scrollIntoView({ block: 'start' });
      } else {
        const target = document.getElementById(id);
        if (target) target.scrollIntoView({ block: 'start' });
      }
    }
    initScrollSpy();
    // Hook: rerender data views when language switches.
    // The toggle UI is wired by autoInitLanguageToggle on DOMContentLoaded.
    window.__rerenderForLang = async () => {
      try {
        const [pubs, pats, news, papers] = await Promise.all([
          loadJSON('publications'), loadJSON('patents'), loadJSON('news'), loadJSON('papers'),
        ]);
        if (pubBox) renderPublications(pubBox, pubs);
        if (patBox) renderPatents(patBox, pats);
        if (newsBox) renderNews(newsBox, news);
        if (paperBox) renderPaperList(paperBox, papers);
      } catch (e) {}
    };
  }
  async function bootNews() {
    const box = document.getElementById('news-root');
    if (!box) return;
    try {
      const items = await loadJSON('news');
      renderNews(box, items);
      window.__rerenderForLang = () => renderNews(box, items);
    } catch (e) { box.textContent = (currentLang() === 'ko' ? '데이터를 불러오지 못했습니다.' : 'Failed to load data.'); }
  }
  async function bootPaperList() {
    const box = document.getElementById('paper-list-root');
    if (!box) return;
    try {
      const papers = await loadJSON('papers');
      renderPaperList(box, papers);
      window.__rerenderForLang = () => renderPaperList(box, papers);
    } catch (e) { box.textContent = (currentLang() === 'ko' ? '데이터를 불러오지 못했습니다.' : 'Failed to load data.'); }
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
    } catch (e) { box.textContent = (currentLang() === 'ko' ? '데이터를 불러오지 못했습니다.' : 'Failed to load data.'); }
  }

  window.Portfolio = { bootHome, bootNews, bootPaperList, bootPaper, initLanguageToggle, currentLang, pickLang };

  // Auto-init the language toggle on any page that includes the UI but doesn't
  // call one of the boot functions (e.g. static career detail pages).
  function autoInitLanguageToggle() {
    if (!document.querySelector('.lang-toggle')) return;
    // If a boot function already wired things up, the active class will already be set.
    const alreadyInit = document.querySelector('.lang-toggle button.active');
    if (alreadyInit) return;
    initLanguageToggle();
  }

  // Career pages: clicking a project card reveals its detail panel below
  // (accordion). One panel visible at a time; first is active by default.
  // Also supports deep links like #proj-elv so a shared URL opens the right
  // project instead of leaving the default (first) one selected.
  function initProjectSelector() {
    const cards = document.querySelectorAll('.proj-card[data-panel]');
    if (!cards.length) return;
    const panels = document.querySelectorAll('.proj-panel[data-panel]');
    const names = Array.from(cards).map((c) => c.dataset.panel);

    function activatePanel(name) {
      if (!names.includes(name)) return false;
      cards.forEach((c) => c.classList.toggle('active', c.dataset.panel === name));
      panels.forEach((p) => p.classList.toggle('active', p.dataset.panel === name));
      return true;
    }

    cards.forEach((card) => {
      card.addEventListener('click', () => activatePanel(card.dataset.panel));
    });

    // Panel ids are "proj-<name>" (e.g. #proj-elv); strip the prefix to match
    // data-panel, then activate and scroll the panel into view.
    function activateFromHash() {
      const h = decodeURIComponent(location.hash.slice(1));
      if (!h) return;
      const name = h.replace(/^proj-/, '');
      if (activatePanel(name)) {
        document.getElementById('proj-' + name)?.scrollIntoView({ block: 'start' });
      }
    }
    activateFromHash();
    window.addEventListener('hashchange', activateFromHash);
  }

  function autoInit() {
    autoInitLanguageToggle();
    initProjectSelector();
    initDocRail();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    autoInit();
  }
})();
