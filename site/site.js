/*
  site/site.js — the reader, the router, and the two maps.

  This file knows how to *display* a claim graph and a search portfolio. It does not know
  any mathematics, any status, any route, or any repository rule: all of that arrives in
  data.json, derived by scripts/site.py from the same validated report scripts/check.py
  prints. Everything user-visible below is chrome — headings, legends, empty states — with
  one deliberate exception noted where it occurs: the relation glosses travel *with* the
  data, so the legend cannot drift from research/program/ledger-schema.md.

  The distinction the interface exists to preserve, and the reason there are two maps
  rather than one:

      Ledger = what is mathematically claimed.
      Portfolio = what the search is doing.
      Checkpoints = why the portfolio changed.

  A route is not a theorem. `completed` means a route's objective ended, never that the
  target was settled; `saturated` is a synthesis judgment about effort, not a fact about
  mathematics. The two maps never share a canvas.
*/

'use strict';

/* ------------------------------------------------------------------ DOM helpers ---- */

const SVG_NS = 'http://www.w3.org/2000/svg';

/** Build an element. Children may be nodes, strings, arrays, or null. */
function el(tag, props, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === 'class') node.className = value;
    else if (key === 'text') node.textContent = value;
    else if (key === 'html') node.appendChild(value);
    else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else if (key === 'dataset') Object.assign(node.dataset, value);
    else node.setAttribute(key, value === true ? '' : String(value));
  }
  append(node, children);
  return node;
}

function svg(tag, props, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(props || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, String(value));
  }
  append(node, children);
  return node;
}

function append(parent, children) {
  for (const child of children.flat(4)) {
    if (child === null || child === undefined || child === false) continue;
    parent.appendChild(typeof child === 'string' ? document.createTextNode(child) : child);
  }
}

function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

/**
 * Place text containing LaTeX `$...$` into the DOM as text, never as markup.
 *
 * The dollar spans are wrapped so MathJax can typeset them if it loaded. When it did
 * not, the source stays on screen and stays readable — which is why the raw text goes in
 * first and typesetting happens afterwards.
 */
function math(text) {
  const fragment = document.createDocumentFragment();
  if (!text) return fragment;
  const parts = String(text).split(/(\$[^$]*\$)/g);
  for (const part of parts) {
    if (!part) continue;
    if (part.startsWith('$') && part.endsWith('$') && part.length > 1) {
      fragment.appendChild(el('span', { class: 'math', text: part }));
    } else {
      fragment.appendChild(document.createTextNode(part));
    }
  }
  return fragment;
}

function typeset(scope) {
  if (window.MathJax && typeof window.MathJax.typesetPromise === 'function') {
    window.MathJax.typesetPromise([scope]).catch(() => { /* source stays visible */ });
  }
}

/* ------------------------------------------------------------------- vocabulary ---- */

/* Presentation only: a glyph and a word for each state, so colour is never the sole
   carrier of meaning. What the states *mean* is the repository's business, not this
   file's — the words below are the repository's own vocabulary, unaltered. */
const STATUS_GLYPH = { proved: '✓', open: '○', refuted: '✗', defined: '≡' };
const ROUTE_GLYPH = {
  queued: '·', active: '▸', blocked: '■', completed: '✓', duplicate: '⧉',
};
const FAMILY_GLYPH = { active: '▸', saturated: '◼', parked: '❙❙' };

const OUTCOME_WORD = {
  'dead-end': 'dead end', directional: 'directional',
  candidate: 'candidate', proposed: 'proposed',
};

let DATA = null;

function statusBadge(status) {
  const known = Object.prototype.hasOwnProperty.call(STATUS_GLYPH, status);
  return el('span', { class: `badge ${known ? status : 'neutral'}` },
    el('span', { class: 'glyph', 'aria-hidden': 'true', text: STATUS_GLYPH[status] || '?' }),
    status || 'unknown');
}

function routeBadge(state) {
  return el('span', { class: 'badge neutral' },
    el('span', { class: 'glyph', 'aria-hidden': 'true', text: ROUTE_GLYPH[state] || '·' }),
    state || 'unknown');
}

function familyBadge(state) {
  return el('span', { class: 'badge neutral' },
    el('span', { class: 'glyph', 'aria-hidden': 'true', text: FAMILY_GLYPH[state] || '·' }),
    state || 'unknown');
}

/* ------------------------------------------------------------------------- links ---- */

function repoBase() {
  const slug = DATA.generated.repository;
  return slug ? `https://github.com/${slug}` : null;
}

/**
 * A permalink into the exact revision on screen, so a link cannot silently move.
 *
 * `source_prefix` turns a path relative to the *published tree* into one relative to the
 * *checkout*. They differ whenever a subtree is published, and without it every source
 * link on such a build is a 404 that looks like a missing file rather than a mis-built
 * site.
 */
function sourceLink(path, line) {
  const base = repoBase();
  if (!base || !path) return null;
  const revision = DATA.generated.commit || DATA.generated.branch || 'HEAD';
  const prefix = DATA.generated.source_prefix || '';
  return `${base}/blob/${revision}/${prefix}${path}${line ? `#L${line}` : ''}`;
}

function idLink(id) {
  if (!id) return null;
  if (DATA.claims[id]) return el('a', { class: 'id', href: `#/node/${id}`, text: id });
  if (DATA.search && DATA.search.routes[id]) {
    return el('a', { class: 'id', href: `#/route/${id}`, text: id });
  }
  if (DATA.memory.candidates.some((entry) => entry.id === id)) {
    return el('a', { class: 'id', href: '#/evidence', text: id });
  }
  return el('code', { class: 'id', text: id });
}

/**
 * The rendered manuscript, at the anchor of one claim.
 *
 * The anchor invariant is what makes this possible without inventing a web-specific id:
 * a ledger node id *is* its manuscript \label, and site/tex4ht.cfg is what carries that
 * through the HTML conversion. When no conversion was attached the answer is null, and
 * the reader is offered the LaTeX source and the PDF instead — never a broken link.
 */
function statementLink(id) {
  const html = DATA.documents && DATA.documents.html;
  return html && html.manuscript ? `${html.manuscript}#${id}` : null;
}

function dossierLinks(artifact) {
  const documents = DATA.documents || {};
  return {
    html: (documents.html && documents.html.dossiers[artifact]) || null,
    pdf: (documents.pdf && documents.pdf.dossiers[artifact]) || null,
  };
}

function fileLink(path, line, label) {
  const href = sourceLink(path, line);
  const text = label || (line ? `${path}:${line}` : path);
  return href ? el('a', { href, class: 'id', text }) : el('code', { class: 'id', text });
}

/**
 * A contribution link into GitHub, carrying the stable id of whatever is on screen.
 *
 * The boundary this respects, and it is the whole point: nothing that arrives through
 * one of these becomes a candidate, a route, a ledger node, a proof record, or a status.
 * It lands in a public inbox and is triaged by the repository's own roles. Popularity is
 * not truth, and a form is not a promotion.
 */
function contribute(template, label, anchor, extra) {
  const base = repoBase();
  if (!base) return null;
  const params = new URLSearchParams({ template, anchor: anchor || '' });
  if (extra) for (const [key, value] of Object.entries(extra)) params.set(key, value);
  return el('a', {
    class: 'action', href: `${base}/issues/new?${params.toString()}`,
    rel: 'noopener', target: '_blank',
  }, label);
}

function discussLink(label) {
  const base = repoBase();
  return base ? el('a', {
    class: 'action', href: `${base}/discussions`, rel: 'noopener', target: '_blank',
  }, label) : null;
}

/* ------------------------------------------------------------------- small parts ---- */

function idList(ids, emptyText) {
  if (!ids || !ids.length) return el('span', { class: 'note', text: emptyText || 'none' });
  return el('ul', { class: 'inline-list' }, ids.map((id) => el('li', {}, idLink(id))));
}

function glossBlock(claim) {
  const source = claim.source || {};
  const rendered = statementLink(claim.id);
  return el('div', {},
    el('span', { class: 'gloss-tag', text: 'One-line gloss — not the statement' }),
    el('p', { class: 'gloss' }, math(claim.gloss)),
    el('p', { class: 'note' },
      'The canonical statement is the ',
      el('code', { class: 'id', text: `\\label{${claim.id}}` }),
      source.file ? [' in ', fileLink(source.file, source.line)] : [],
      '. If the two disagree, the manuscript is right and this line is the defect.'),
    el('div', { class: 'actions' },
      rendered
        ? el('a', { class: 'action', href: rendered }, 'Read the statement')
        : null,
      DATA.documents && DATA.documents.pdf && DATA.documents.pdf.manuscript
        ? el('a', { class: 'action', href: DATA.documents.pdf.manuscript, target: '_blank' },
          'Manuscript (PDF)') : null));
}

function statCard(value, label) {
  return el('div', { class: 'card stat' },
    el('span', { class: 'value', text: String(value) }),
    el('span', { class: 'label', text: label }));
}

function emptyState(text) { return el('p', { class: 'empty', text }); }

/* -------------------------------------------------------------------------- maps ---- */

const NODE_W = 212;
const NODE_H = 56;

/**
 * Draw one graph. Layout arrives precomputed and deterministic from the exporter —
 * geometry here is navigation only. Proximity, centrality and column position carry no
 * mathematical meaning whatever, and no interaction in this function creates any.
 */
function graph({ nodes, edges, legend, focusId, selectHandler, stageNote }) {
  const state = {
    focus: focusId || null,
    depth: 1,
    scope: nodes.length > 14 ? 'neighbourhood' : 'all',
    off: new Set(),
    selected: null,
  };

  const stage = el('div', { class: 'map-stage' });
  const controls = el('div', { class: 'map-controls' });
  const legendBar = el('div', { class: 'legend' });
  const wrapper = el('div', { class: 'map' }, controls, stage, legendBar);
  const detail = el('div', {});
  const container = el('div', {}, wrapper, detail);

  const byId = new Map(nodes.map((node) => [node.id, node]));
  const adjacency = new Map(nodes.map((node) => [node.id, new Set()]));
  for (const edge of edges) {
    if (adjacency.has(edge.from)) adjacency.get(edge.from).add(edge.to);
    if (adjacency.has(edge.to)) adjacency.get(edge.to).add(edge.from);
  }

  function visible() {
    if (state.scope === 'all' || !state.focus || !byId.has(state.focus)) {
      return new Set(byId.keys());
    }
    let frontier = new Set([state.focus]);
    const seen = new Set(frontier);
    for (let step = 0; step < state.depth; step += 1) {
      const next = new Set();
      for (const id of frontier) {
        for (const other of adjacency.get(id) || []) {
          if (!seen.has(other)) { seen.add(other); next.add(other); }
        }
      }
      frontier = next;
    }
    return seen;
  }

  /* --- controls ------------------------------------------------------------------ */

  const scopeSelect = el('select', {
    'aria-label': 'How much of the map to show',
    onchange: (event) => { state.scope = event.target.value; refit(); },
  },
    el('option', { value: 'neighbourhood', text: 'Neighbourhood of…' }),
    el('option', { value: 'all', text: 'Whole map' }));
  scopeSelect.value = state.scope;

  const focusSelect = el('select', {
    'aria-label': 'Centre of the neighbourhood',
    onchange: (event) => { state.focus = event.target.value; refit(); },
  }, nodes.map((node) => el('option', { value: node.id, text: node.id })));
  if (state.focus) focusSelect.value = state.focus;

  const depthSelect = el('select', {
    'aria-label': 'How many steps out',
    onchange: (event) => { state.depth = Number(event.target.value); refit(); },
  }, [1, 2, 3].map((n) => el('option', { value: n, text: `${n} step${n > 1 ? 's' : ''}` })));

  const search = el('input', {
    type: 'search', placeholder: 'find an id…', 'aria-label': 'Find a node by id',
    oninput: (event) => {
      const query = event.target.value.trim().toLowerCase();
      if (!query) { state.selected = null; draw(); return; }
      const hit = nodes.find((node) => node.id.toLowerCase().includes(query));
      if (hit) { state.focus = hit.id; focusSelect.value = hit.id; select(hit.id); }
    },
  });

  const toggles = el('div', { class: 'group' },
    legend.map((entry) => el('label', { title: entry.gloss || '' },
      el('input', {
        type: 'checkbox', checked: true,
        onchange: (event) => {
          if (event.target.checked) state.off.delete(entry.key); else state.off.add(entry.key);
          draw();
        },
      }),
      entry.label)));

  const zoomButtons = el('div', { class: 'group' },
    el('button', { type: 'button', class: 'action', 'aria-label': 'Zoom in',
      onclick: () => zoom(1 / 1.25) }, '+'),
    el('button', { type: 'button', class: 'action', 'aria-label': 'Zoom out',
      onclick: () => zoom(1.25) }, '−'),
    el('button', { type: 'button', class: 'action',
      onclick: () => refit() }, 'Fit'));

  append(controls, [
    el('div', { class: 'group' }, scopeSelect, focusSelect, depthSelect),
    el('div', { class: 'group' }, search),
    toggles,
    zoomButtons,
  ]);

  append(legendBar, [
    legend.map((entry) => el('span', { class: 'key', title: entry.gloss || '' },
      el('span', { class: `swatch ${entry.key}`, 'aria-hidden': 'true' }), entry.label)),
    el('span', { class: 'key', text: 'arrow reads: source → target, in the direction the relation is stored' }),
  ]);

  /* --- selection ------------------------------------------------------------------ */

  function select(id) {
    state.selected = id;
    draw();
    clear(detail);
    if (id && selectHandler) detail.appendChild(selectHandler(id));
    typeset(detail);
  }

  /* --- drawing -------------------------------------------------------------------- */

  let view = null;
  let canvas = null;

  /** Forget the viewport, so the next draw frames whatever is now shown. */
  function refit() { view = null; draw(); }

  function zoom(factor) {
    if (!view || !canvas) return;
    const cx = view.x + view.w / 2;
    const cy = view.y + view.h / 2;
    view.w *= factor;
    view.h *= factor;
    view.x = cx - view.w / 2;
    view.y = cy - view.h / 2;
    canvas.setAttribute('viewBox', `${view.x} ${view.y} ${view.w} ${view.h}`);
  }

  function boxEdge(from, to) {
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    if (dx === 0 && dy === 0) return from;
    const scale = Math.min(
      Math.abs(dx) < 1e-6 ? Infinity : (NODE_W / 2) / Math.abs(dx),
      Math.abs(dy) < 1e-6 ? Infinity : (NODE_H / 2) / Math.abs(dy));
    return { x: from.x + dx * scale, y: from.y + dy * scale };
  }

  function draw() {
    const shown = visible();
    clear(stage);

    const placed = nodes.filter((node) => shown.has(node.id));
    if (!placed.length) {
      stage.appendChild(emptyState('Nothing to draw here yet.'));
      return;
    }
    const minX = Math.min(...placed.map((n) => n.x)) - NODE_W;
    const maxX = Math.max(...placed.map((n) => n.x)) + NODE_W;
    const minY = Math.min(...placed.map((n) => n.y)) - NODE_H;
    const maxY = Math.max(...placed.map((n) => n.y)) + NODE_H;
    if (!view) view = { x: minX, y: minY, w: maxX - minX, h: maxY - minY };

    canvas = svg('svg', {
      viewBox: `${view.x} ${view.y} ${view.w} ${view.h}`,
      role: 'group', 'aria-label': 'Graph. Use the list below the map for a linear reading.',
    });

    const defs = svg('defs', {});
    for (const entry of legend) {
      defs.appendChild(svg('marker', {
        id: `arrow-${entry.key}`, viewBox: '0 0 10 10', refX: 9, refY: 5,
        markerWidth: 6, markerHeight: 6, orient: 'auto-start-reverse',
      }, svg('path', { d: 'M 0 0 L 10 5 L 0 10 z', class: `marker ${entry.key}`,
        fill: 'context-stroke' })));
    }
    canvas.appendChild(defs);

    const edgeLayer = svg('g', {});
    const nodeLayer = svg('g', {});
    canvas.appendChild(edgeLayer);
    canvas.appendChild(nodeLayer);

    for (const edge of edges) {
      if (state.off.has(edge.kind)) continue;
      if (!shown.has(edge.from) || !shown.has(edge.to)) continue;
      const a = byId.get(edge.from);
      const b = byId.get(edge.to);
      if (!a || !b) continue;
      const start = boxEdge(a, b);
      const end = boxEdge(b, a);
      const dim = state.selected
        && edge.from !== state.selected && edge.to !== state.selected;
      edgeLayer.appendChild(svg('line', {
        x1: start.x, y1: start.y, x2: end.x, y2: end.y,
        class: `gedge ${edge.kind}${dim ? ' dimmed' : ''}`,
        'marker-end': `url(#arrow-${edge.kind})`,
      }, svg('title', {}, `${edge.from} — ${edge.label} → ${edge.to}`)));
    }

    for (const node of placed) {
      const dim = state.selected && state.selected !== node.id
        && !(adjacency.get(state.selected) || new Set()).has(node.id);
      const classes = ['gnode', node.tone || 'neutral'];
      if (node.isTarget) classes.push('is-target');
      if (state.selected === node.id) classes.push('selected');
      if (dim) classes.push('dimmed');
      const group = svg('g', {
        class: classes.join(' '), tabindex: '0', role: 'button',
        'aria-label': `${node.id}, ${node.meta}`,
        transform: `translate(${node.x - NODE_W / 2} ${node.y - NODE_H / 2})`,
        onclick: () => select(node.id),
        onkeydown: (event) => {
          if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(node.id); }
        },
      },
        svg('rect', { class: 'box', width: NODE_W, height: NODE_H, rx: 8 }),
        svg('text', { class: 'glabel', x: 12, y: 22 }, node.id),
        svg('text', { class: 'gmeta', x: 12, y: 40 }, node.meta),
        node.isTarget ? svg('text', { class: 'gkind', x: NODE_W - 12, y: 22,
          'text-anchor': 'end' }, 'target') : null);
      nodeLayer.appendChild(group);
    }

    stage.appendChild(canvas);
    stage.appendChild(el('span', { class: 'map-hint',
      text: stageNote || 'drag to pan · scroll to zoom · click a box' }));
    wirePanZoom();
  }

  function wirePanZoom() {
    let dragging = null;
    canvas.addEventListener('pointerdown', (event) => {
      if (event.target.closest('.gnode')) return;
      dragging = { x: event.clientX, y: event.clientY };
      canvas.classList.add('dragging');
      canvas.setPointerCapture(event.pointerId);
    });
    canvas.addEventListener('pointermove', (event) => {
      if (!dragging) return;
      const rect = canvas.getBoundingClientRect();
      view.x -= (event.clientX - dragging.x) * (view.w / rect.width);
      view.y -= (event.clientY - dragging.y) * (view.h / rect.height);
      dragging = { x: event.clientX, y: event.clientY };
      canvas.setAttribute('viewBox', `${view.x} ${view.y} ${view.w} ${view.h}`);
    });
    const stop = () => { dragging = null; canvas.classList.remove('dragging'); };
    canvas.addEventListener('pointerup', stop);
    canvas.addEventListener('pointercancel', stop);
    canvas.addEventListener('wheel', (event) => {
      event.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const factor = event.deltaY > 0 ? 1.12 : 1 / 1.12;
      const px = view.x + ((event.clientX - rect.left) / rect.width) * view.w;
      const py = view.y + ((event.clientY - rect.top) / rect.height) * view.h;
      view.x = px - (px - view.x) * factor;
      view.y = py - (py - view.y) * factor;
      view.w *= factor;
      view.h *= factor;
      canvas.setAttribute('viewBox', `${view.x} ${view.y} ${view.w} ${view.h}`);
    }, { passive: false });
  }

  draw();
  if (focusId) select(focusId);
  return container;
}

/* --------------------------------------------------------------- the claim map ----- */

function claimGraphModel() {
  const layout = DATA.layout.claims;
  const target = DATA.program.target;
  const nodes = Object.values(DATA.claims).map((claim) => ({
    id: claim.id,
    x: (layout[claim.id] || { x: 0 }).x,
    y: -(layout[claim.id] || { y: 0 }).y,
    tone: claim.status,
    meta: `${claim.kind || '?'} · ${claim.status || '?'}`,
    isTarget: claim.id === target,
  }));
  const edges = [];
  for (const claim of Object.values(DATA.claims)) {
    for (const relation of DATA.vocabulary.relations) {
      for (const other of claim.edges[relation.field] || []) {
        if (!DATA.claims[other]) continue;
        edges.push({
          from: claim.id, to: other, kind: relation.class, label: relation.label,
        });
      }
    }
  }
  const used = new Set(edges.map((edge) => edge.kind));
  const legend = DATA.vocabulary.relations
    .filter((relation) => used.has(relation.class))
    .filter((relation, index, all) =>
      all.findIndex((other) => other.class === relation.class) === index)
    .map((relation) => ({ key: relation.class, label: relation.label, gloss: relation.gloss }));
  return { nodes, edges, legend };
}

/* -------------------------------------------------------------- the search map ----- */

function searchGraphModel() {
  const search = DATA.search;
  if (!search) return null;
  const layout = DATA.layout.search;
  const nodes = [];
  for (const family of Object.values(search.families)) {
    nodes.push({
      id: family.id,
      x: (layout[family.id] || { x: 0 }).x,
      y: -(layout[family.id] || { y: 0 }).y,
      tone: 'neutral',
      meta: `family · ${family.state || '?'}`,
    });
  }
  for (const route of Object.values(search.routes)) {
    nodes.push({
      id: route.id,
      x: (layout[route.id] || { x: 0 }).x,
      y: -(layout[route.id] || { y: 0 }).y,
      tone: 'neutral',
      meta: `route · ${route.state || '?'}`,
    });
  }
  const edges = [];
  for (const route of Object.values(search.routes)) {
    if (route.family && search.families[route.family] && !route.parent) {
      edges.push({ from: route.family, to: route.id, kind: 'family', label: 'contains' });
    }
    if (route.parent && search.routes[route.parent]) {
      edges.push({ from: route.parent, to: route.id, kind: 'family', label: 'grew into' });
    }
    for (const relation of route.related) {
      if (!search.routes[relation.to]) continue;
      edges.push({
        from: route.id, to: relation.to, kind: relation.relation, label: relation.relation,
      });
    }
  }
  const used = new Set(edges.map((edge) => edge.kind));
  const legend = [
    { key: 'family', label: 'family / parent', gloss: 'Which family a route belongs to, and which route it grew out of.' },
    { key: 'overlaps', label: 'overlaps', gloss: 'Two routes cover some of the same ground.' },
    { key: 'duplicates', label: 'duplicates', gloss: 'The same idea as another route. Both may not be active.' },
    { key: 'refines', label: 'refines', gloss: 'A sharper version of another route.' },
  ].filter((entry) => used.has(entry.key));
  return { nodes, edges, legend };
}

/* ------------------------------------------------------------------------- views ---- */

function viewTarget() {
  const page = el('div', {});
  const program = DATA.program;

  // Two different "not ready" states, and telling a reader they are the same would be
  // the first thing on the page that is false. A tree with no claims is a fresh clone;
  // a tree with claims and no brief is a repository that has not opened a search yet.
  if (!Object.keys(DATA.claims).length) {
    page.appendChild(el('div', { class: 'banner' },
      el('strong', { text: 'This repository is still an uninstantiated template. ' }),
      'It is structurally valid and states nothing yet, which is the correct state for a '
      + 'fresh clone rather than a defect. Nothing below describes a live search.'));
  } else if (!program.target) {
    page.appendChild(el('div', { class: 'banner' },
      el('strong', { text: 'No target is named. ' }),
      'This repository states claims but has no problem brief, so nothing here says '
      + 'what the search is aimed at or what would finish it. The mathematics below is '
      + 'real; the search around it has not been opened.'));
  }

  const target = program.target ? DATA.claims[program.target] : null;

  page.appendChild(el('h1', {}, target ? 'The target' : 'This repository'));
  if (program.scope) {
    page.appendChild(el('p', { class: 'lede' }, math(program.scope)));
  }

  if (target) {
    const proofCount = target.proofs.length;
    page.appendChild(el('div', { class: 'card' },
      el('div', { class: 'badges' },
        el('a', { class: 'id', href: `#/node/${target.id}`, text: target.id }),
        el('span', { class: 'badge kind', text: target.kind || 'unknown kind' }),
        statusBadge(target.status),
        target.provenance ? el('span', { class: 'badge kind', text: target.provenance }) : null),
      el('div', { style: 'margin-top:.8rem' }, glossBlock(target)),
      el('div', { class: 'actions' },
        el('a', { class: 'action', href: `#/node/${target.id}` }, 'Open the claim'),
        program.brief ? (() => {
          const link = sourceLink(program.brief);
          return link ? el('a', { class: 'action', href: link, rel: 'noopener', target: '_blank' },
            'Problem brief — what would finish this') : null;
        })() : null,
        proofCount ? null : discussLink('Discuss'))));
  }

  /* --- state of the search ------------------------------------------------------- */

  const claims = Object.values(DATA.claims);
  const counts = {};
  for (const claim of claims) counts[claim.status] = (counts[claim.status] || 0) + 1;
  const routes = DATA.search ? Object.values(DATA.search.routes) : [];
  const live = routes.filter((route) => ['active', 'queued'].includes(route.state));
  const blocked = routes.filter((route) => route.state === 'blocked');
  const heads = DATA.memory.checkpoints.filter((record) => !record.superseded_by.length);

  page.appendChild(el('h2', { text: 'Where the search stands' }));
  page.appendChild(el('div', { class: 'grid three' },
    statCard(claims.length, `claim${claims.length === 1 ? '' : 's'} in the ledger`),
    statCard(counts.proved || 0, 'proved, each with a certified dossier'),
    statCard(counts.open || 0, 'open'),
    statCard(counts.refuted || 0, 'refuted'),
    statCard(live.length, 'route(s) live'),
    statCard(blocked.length, 'route(s) blocked')));

  /* --- blockers ------------------------------------------------------------------ */

  page.appendChild(el('h2', { text: 'What is holding the search up' }));
  if (!blocked.length) {
    page.appendChild(emptyState('No route is recorded as blocked.'));
  } else {
    page.appendChild(el('ul', { class: 'rows' }, blocked.map((route) => el('li', {},
      el('div', { class: 'row-head' },
        el('a', { class: 'id', href: `#/route/${route.id}`, text: route.id }),
        routeBadge(route.state),
        el('span', { class: 'note' }, 'blocked on ', idLink(route.blocker))),
      route.objective ? el('p', { class: 'row-body' }, math(route.objective)) : null,
      route.reopen_if ? el('p', { class: 'row-note' }, 'Reopens if: ', math(route.reopen_if)) : null))));
  }

  /* --- live routes --------------------------------------------------------------- */

  page.appendChild(el('h2', { text: 'What is being tried' }));
  if (!DATA.search) {
    page.appendChild(emptyState(
      'No search portfolio. A repository with one target and one live route coordinates '
      + 'itself; the portfolio is created when several routes, agents or sessions are in '
      + 'flight at once.'));
  } else if (!live.length) {
    page.appendChild(emptyState('No route is active or queued.'));
  } else {
    page.appendChild(el('ul', { class: 'rows' }, live.map((route) => el('li', {},
      el('div', { class: 'row-head' },
        el('a', { class: 'id', href: `#/route/${route.id}`, text: route.id }),
        routeBadge(route.state)),
      route.objective ? el('p', { class: 'row-body' }, math(route.objective)) : null))));
  }

  /* --- recent durable advances --------------------------------------------------- */

  page.appendChild(el('div', { class: 'section-head' },
    el('h2', { text: 'Recent durable records' }),
    el('a', { href: '#/evidence', text: 'All evidence →' })));
  if (!heads.length) {
    page.appendChild(emptyState('No checkpoints recorded yet.'));
  } else {
    page.appendChild(el('ul', { class: 'rows' }, heads.slice(0, 5).map(checkpointRow)));
  }

  /* --- entries into the maps ------------------------------------------------------ */

  page.appendChild(el('h2', { text: 'Two maps, deliberately not one' }));
  page.appendChild(el('div', { class: 'grid two' },
    el('div', { class: 'card' },
      el('h3', { text: 'Mathematics' }),
      el('p', { class: 'note' },
        'What is claimed: statements, proof dependencies, implication antecedents, '
        + 'refinements, refutations, and the two kinds of obstruction. Everything here '
        + 'has a truth status and a provenance.'),
      el('div', { class: 'actions' }, el('a', { class: 'action', href: '#/claims' }, 'Open the claim graph'))),
    el('div', { class: 'card' },
      el('h3', { text: 'Search' }),
      el('p', { class: 'note' },
        'What the search is doing: approach families, routes, blockers, and the '
        + 'checkpoints that explain why a route changed state. None of it is a claim — '
        + 'a completed route settles nothing by itself, and saturation is a judgment '
        + 'about effort.'),
      el('div', { class: 'actions' }, el('a', { class: 'action', href: '#/search' }, 'Open the search map')))));

  /* --- contribute ----------------------------------------------------------------- */

  if (repoBase()) {
    page.appendChild(el('h2', { text: 'Where another mathematician could help' }));
    page.appendChild(el('p', { class: 'note' },
      'Everything below opens a public inbox. Nothing that arrives through it becomes a '
      + 'candidate, a route, a claim, a proof record, or a status by itself — it is '
      + 'triaged by the repository’s own roles, and proofs still pass through a '
      + 'standalone dossier and independent certification.'));
    page.appendChild(el('div', { class: 'actions' },
      contribute('proof-gap.yml', 'Report a proof gap', program.target),
      contribute('counterexample.yml', 'Propose a counterexample', program.target),
      contribute('literature-lead.yml', 'Point at existing work', program.target),
      contribute('route-proposal.yml', 'Propose an approach', program.target),
      discussLink('Ask a question')));
  }

  return page;
}

function viewClaims() {
  const page = el('div', {});
  page.appendChild(el('h1', { text: 'The mathematical map' }));
  page.appendChild(el('p', { class: 'lede' },
    'Every statement this program has committed to, and how they rest on each other. '
    + 'Truth and applicability are separate: a proved implication whose antecedent is '
    + 'open is still proved, and its antecedent is drawn as an assumption, never as a '
    + 'proof dependency.'));

  const claims = Object.values(DATA.claims);
  if (!claims.length) {
    page.appendChild(emptyState('This ledger has no nodes yet.'));
    return page;
  }

  const model = claimGraphModel();
  page.appendChild(graph({
    ...model,
    focusId: DATA.program.target || model.nodes[0].id,
    selectHandler: (id) => claimSummaryCard(DATA.claims[id]),
    stageNote: 'dependencies sit below what rests on them',
  }));

  page.appendChild(el('h2', { text: 'Every claim, as a list' }));
  page.appendChild(el('ul', { class: 'rows' }, claims
    .slice()
    .sort((a, b) => a.id.localeCompare(b.id))
    .map((claim) => el('li', {},
      el('div', { class: 'row-head' },
        el('a', { class: 'id', href: `#/node/${claim.id}`, text: claim.id }),
        el('span', { class: 'badge kind', text: claim.kind || '?' }),
        statusBadge(claim.status),
        claim.applicability_blocked_by.length
          ? el('span', { class: 'badge warn' }, 'applicability-blocked') : null,
        claim.id === DATA.program.target ? el('span', { class: 'badge neutral', text: 'target' }) : null),
      el('p', { class: 'row-body' }, math(claim.gloss))))));
  return page;
}

function claimSummaryCard(claim) {
  if (!claim) return el('div', {});
  return el('div', { class: 'card', style: 'margin-top:1rem' },
    el('div', { class: 'badges' },
      el('a', { class: 'id', href: `#/node/${claim.id}`, text: claim.id }),
      el('span', { class: 'badge kind', text: claim.kind || '?' }),
      statusBadge(claim.status)),
    el('p', { class: 'row-body gloss' }, math(claim.gloss)),
    el('div', { class: 'actions' },
      el('a', { class: 'action', href: `#/node/${claim.id}` }, 'Full record')));
}

function viewSearch() {
  const page = el('div', {});
  page.appendChild(el('h1', { text: 'The search map' }));
  page.appendChild(el('p', { class: 'lede' },
    'What the search is doing, which is not what is true. A family is a mechanism; a '
    + 'route is one attempt within it. "Completed" means a route’s objective '
    + 'ended, not that anything was settled, and "saturated" is a judgment about effort '
    + 'that carries a reopening condition.'));

  if (!DATA.search) {
    page.appendChild(emptyState(
      'This repository has no search portfolio. That is a normal state: a portfolio is '
      + 'created when several routes, agents or sessions are in flight at once, and one '
      + 'describing a search nobody is running is overhead.'));
    return page;
  }

  const model = searchGraphModel();
  if (model.nodes.length) {
    page.appendChild(graph({
      ...model,
      focusId: model.nodes[0].id,
      selectHandler: (id) => (DATA.search.routes[id]
        ? routeSummaryCard(DATA.search.routes[id])
        : familySummaryCard(DATA.search.families[id])),
      stageNote: 'families on top, routes beneath them',
    }));
  }

  page.appendChild(el('h2', { text: 'Families and their routes' }));
  for (const family of Object.values(DATA.search.families)) {
    page.appendChild(el('div', { class: 'card', style: 'margin-bottom:1rem' },
      el('div', { class: 'badges' },
        el('code', { class: 'id', text: family.id }),
        familyBadge(family.state)),
      family.mechanism ? el('p', { class: 'row-body' }, math(family.mechanism)) : null,
      family.reopen_if
        ? el('p', { class: 'row-note' }, 'Reopens if: ', math(family.reopen_if)) : null,
      family.closure_checkpoint
        ? el('p', { class: 'row-note' }, 'Closed at ', fileLink(family.closure_checkpoint)) : null,
      el('ul', { class: 'rows', style: 'margin-top:.8rem' },
        family.routes.map((id) => routeRow(DATA.search.routes[id])))));
  }
  return page;
}

function routeRow(route) {
  if (!route) return null;
  return el('li', { class: 'tight' },
    el('div', { class: 'row-head' },
      el('a', { class: 'id', href: `#/route/${route.id}`, text: route.id }),
      routeBadge(route.state),
      route.parent ? el('span', { class: 'note' }, 'from ', idLink(route.parent)) : null,
      route.blocker ? el('span', { class: 'note' }, 'blocked on ', idLink(route.blocker)) : null),
    route.objective ? el('p', { class: 'row-body' }, math(route.objective)) : null);
}

function routeSummaryCard(route) {
  return el('div', { class: 'card', style: 'margin-top:1rem' },
    el('div', { class: 'badges' },
      el('a', { class: 'id', href: `#/route/${route.id}`, text: route.id }),
      routeBadge(route.state)),
    route.objective ? el('p', { class: 'row-body' }, math(route.objective)) : null,
    el('div', { class: 'actions' },
      el('a', { class: 'action', href: `#/route/${route.id}` }, 'Full record')));
}

function familySummaryCard(family) {
  if (!family) return el('div', {});
  return el('div', { class: 'card', style: 'margin-top:1rem' },
    el('div', { class: 'badges' },
      el('code', { class: 'id', text: family.id }),
      familyBadge(family.state)),
    family.mechanism ? el('p', { class: 'row-body' }, math(family.mechanism)) : null);
}

/* ---------------------------------------------------------------- node detail ------ */

function proofCard(proof) {
  const detail = proof.review_detail;
  const agent = proof.mode === 'agent';
  const links = dossierLinks(proof.artifact);
  return el('li', {},
    el('div', { class: 'row-head' },
      el('span', { class: 'badge neutral', text: `mode: ${proof.mode || '?'}` }),
      fileLink(proof.artifact, null, proof.artifact),
      links.html ? el('a', { class: 'action', href: links.html }, 'Read it') : null,
      links.pdf ? el('a', { class: 'action', href: links.pdf, target: '_blank' }, 'PDF') : null),
    agent
      ? el('div', {},
        el('p', { class: 'row-body' },
          'Certified by an independent review on disk: ',
          fileLink(proof.review, null, proof.review), '.'),
        detail ? el('dl', { class: 'kv' },
          el('dt', { text: 'verdict' }), el('dd', { text: detail.verdict || '—' }),
          el('dt', { text: 'reviewer' }), el('dd', { text: detail.reviewer || '—' }),
          el('dt', { text: 'author(s)' }), el('dd', { text: detail.authors.join(', ') || '—' }),
          el('dt', { text: 'dated' }), el('dd', { text: detail.date || '—' })) : null)
      : el('p', { class: 'row-body' },
        'Accepted by ',
        el('strong', { text: proof.accepted_by || 'an unnamed person' }),
        '. A human acceptance is an attestation: unlike an agent certification it '
        + 'carries no persisted review report in the repository, and this page does not '
        + 'present the two as equal evidence.'));
}

function viewNode(id) {
  const claim = DATA.claims[id];
  const page = el('div', {});
  if (!claim) {
    page.appendChild(el('h1', { text: 'No such claim' }));
    page.appendChild(el('p', { class: 'lede' },
      'Nothing in this ledger has the id ', el('code', { class: 'id', text: id }), '. It '
      + 'may have been a candidate that was never promoted, or a route — those live '
      + 'on the search map.'));
    page.appendChild(el('div', { class: 'actions' },
      el('a', { class: 'action', href: '#/claims' }, 'The claim graph'),
      el('a', { class: 'action', href: '#/search' }, 'The search map')));
    return page;
  }

  page.appendChild(el('div', { class: 'detail-head' },
    el('p', { class: 'crumb' }, el('a', { href: '#/claims', text: 'Mathematics' }), ' / ', claim.id),
    el('h1', { text: claim.id }),
    el('div', { class: 'badges' },
      el('span', { class: 'badge kind', text: claim.kind || '?' }),
      statusBadge(claim.status),
      el('span', { class: 'badge kind', text: claim.provenance || 'unknown provenance' }),
      claim.import_class ? el('span', { class: 'badge kind', text: claim.import_class }) : null,
      claim.id === DATA.program.target ? el('span', { class: 'badge neutral', text: 'target' }) : null,
      claim.applicability_blocked_by.length
        ? el('span', { class: 'badge warn' }, 'applicability-blocked') : null)));

  page.appendChild(el('div', { class: 'card' }, glossBlock(claim)));

  /* --- what fences it ------------------------------------------------------------- */

  const hard = claim.edges.bounded_by || [];
  const soft = claim.edges.heuristic_barriers || [];
  if (hard.length || soft.length) {
    page.appendChild(el('h2', { text: 'Obstructions' }));
    const cards = [];
    if (hard.length) {
      cards.push(el('div', { class: 'card fence hard' },
        el('span', { class: 'fence-label', text: 'Hard fence — proved' }),
        el('p', { class: 'row-body' },
          'A statement violating one of these is wrong by construction.'),
        idList(hard)));
    }
    if (soft.length) {
      cards.push(el('div', { class: 'card fence soft' },
        el('span', { class: 'fence-label', text: 'Heuristic barrier — advisory' }),
        el('p', { class: 'row-body' },
          'These guide work and fence nothing logically. An open obstruction is a '
          + 'method barrier somebody expects to bite, not a proved impossibility.'),
        idList(soft)));
    }
    page.appendChild(el('div', { class: 'grid two' }, cards));
  }

  /* --- truth vs applicability ------------------------------------------------------ */

  page.appendChild(el('h2', { text: 'How it sits in the graph' }));
  const relationRows = [];
  for (const relation of DATA.vocabulary.relations) {
    if (relation.field === 'bounded_by' || relation.field === 'heuristic_barriers') continue;
    const forward = claim.edges[relation.field] || [];
    const reverseSpec = DATA.vocabulary.reverse[relation.field];
    const backward = reverseSpec ? claim.reverse[reverseSpec.field] || [] : [];
    if (!forward.length && !backward.length) continue;
    relationRows.push(el('div', { class: 'card' },
      el('h3', { text: relation.label }),
      el('p', { class: 'note', text: relation.gloss }),
      el('dl', { class: 'kv' },
        el('dt', { text: relation.label }), el('dd', {}, idList(forward)),
        reverseSpec ? el('dt', { text: reverseSpec.label }) : null,
        reverseSpec ? el('dd', {}, idList(backward)) : null)));
  }
  page.appendChild(relationRows.length
    ? el('div', { class: 'grid two' }, relationRows)
    : emptyState('This claim stands on its own: no recorded relation to another node.'));

  if (claim.applicability_blocked_by.length) {
    page.appendChild(el('div', { class: 'card', style: 'margin-top:1rem' },
      el('h3', { text: 'Applicability' }),
      el('p', { class: 'row-body' },
        'This is proved, and its antecedents are not. That does not weaken the proof: '
        + 'the implication holds; what it can be applied to is what is blocked.'),
      idList(claim.applicability_blocked_by)));
  }

  /* --- certification --------------------------------------------------------------- */

  page.appendChild(el('h2', { text: 'Certification' }));
  if (claim.proofs.length) {
    page.appendChild(el('ul', { class: 'rows' }, claim.proofs.map(proofCard)));
  } else if (claim.status === 'refuted') {
    page.appendChild(el('div', { class: 'card' },
      el('p', { class: 'row-body' },
        'This statement is refuted. A refuted node has no proof: it names its proved '
        + 'refuters, each of which is an ordinary node carrying an ordinary certified '
        + 'dossier of its own.'),
      idList(claim.edges.refuted_by)));
  } else {
    page.appendChild(emptyState(
      claim.status === 'open'
        ? 'Open. No proof is recorded — this is the work that remains.'
        : 'No proof record.'));
  }

  if (claim.references.length) {
    page.appendChild(el('h2', { text: 'References' }));
    page.appendChild(el('ul', { class: 'inline-list' },
      claim.references.map((key) => el('li', {}, el('code', { class: 'id', text: key })))));
  }

  /* --- the search around it -------------------------------------------------------- */

  page.appendChild(el('h2', { text: 'The search around it' }));
  const around = [];
  if (claim.blocks_routes.length) {
    around.push(el('div', { class: 'card' },
      el('h3', { text: 'Routes blocked on this' }),
      el('ul', { class: 'rows' },
        claim.blocks_routes.map((id) => routeRow(DATA.search.routes[id])))));
  }
  if (claim.checkpoints.length) {
    around.push(el('div', { class: 'card' },
      el('h3', { text: 'Checkpoints that engaged it' }),
      el('ul', { class: 'rows' }, claim.checkpoints.map((path) =>
        checkpointRow(DATA.memory.checkpoints.find((record) => record.path === path))))));
  }
  page.appendChild(around.length
    ? el('div', { class: 'grid two' }, around)
    : emptyState('No route is blocked on this and no checkpoint has engaged it.'));

  /* --- contribute ------------------------------------------------------------------ */

  if (repoBase()) {
    page.appendChild(el('h2', { text: 'Contribute to this claim' }));
    page.appendChild(el('div', { class: 'actions' },
      claim.proofs.length ? contribute('proof-gap.yml', 'Report a gap in this proof', claim.id) : null,
      claim.status !== 'refuted' ? contribute('counterexample.yml', 'Propose a counterexample', claim.id) : null,
      contribute('literature-lead.yml', 'Point at existing work', claim.id),
      contribute('correction.yml', 'Report an error on this page', claim.id),
      discussLink('Discuss this claim')));
    page.appendChild(el('p', { class: 'note', style: 'margin-top:.6rem' },
      'A proof or refutation enters the same way here as anywhere else in this '
      + 'repository: a standalone dossier and an independent certification. Nothing '
      + 'reaches this page’s status field by acclamation.'));
  }

  return page;
}

/* --------------------------------------------------------------- route detail ------ */

function viewRoute(id) {
  const page = el('div', {});
  const route = DATA.search && DATA.search.routes[id];
  if (!route) {
    page.appendChild(el('h1', { text: 'No such route' }));
    page.appendChild(el('p', { class: 'lede' },
      'The portfolio has no route ', el('code', { class: 'id', text: id }),
      '. Routes are transient by design and this one may never have existed; the '
      + 'portfolio records what the search is doing now, not everything it ever did.'));
    page.appendChild(el('div', { class: 'actions' },
      el('a', { class: 'action', href: '#/search' }, 'The search map')));
    return page;
  }
  const family = DATA.search.families[route.family];

  page.appendChild(el('div', { class: 'detail-head' },
    el('p', { class: 'crumb' }, el('a', { href: '#/search', text: 'Search' }), ' / ', route.id),
    el('h1', { text: route.id }),
    el('div', { class: 'badges' },
      routeBadge(route.state),
      family ? el('span', { class: 'badge kind', text: family.id }) : null)));

  page.appendChild(el('div', { class: 'card' },
    el('span', { class: 'gloss-tag', text: 'Objective — an intention, never a claim' }),
    el('p', { class: 'gloss' }, math(route.objective || '—')),
    el('p', { class: 'note' },
      'A route has no truth value. "Completed" would mean this route’s objective '
      + 'is finished and there is nothing left to try along it — it says nothing about '
      + 'whether the target is settled.')));

  if (family) {
    page.appendChild(el('h2', { text: 'Its family' }));
    page.appendChild(el('div', { class: 'card' },
      el('div', { class: 'badges' },
        el('code', { class: 'id', text: family.id }), familyBadge(family.state)),
      family.mechanism ? el('p', { class: 'row-body' }, math(family.mechanism)) : null,
      family.reopen_if ? el('p', { class: 'row-note' }, 'Family reopens if: ', math(family.reopen_if)) : null,
      family.closure_checkpoint
        ? el('p', { class: 'row-note' }, 'Closed at ', fileLink(family.closure_checkpoint)) : null));
  }

  if (route.state === 'blocked') {
    page.appendChild(el('h2', { text: 'What it is stuck on' }));
    page.appendChild(el('div', { class: 'card fence hard' },
      el('p', { class: 'row-head' }, 'Blocked on ', idLink(route.blocker)),
      route.reopen_if ? el('p', { class: 'row-body' }, 'Reopens if: ', math(route.reopen_if)) : null,
      el('p', { class: 'note' },
        'The blocker is named, never restated here. If it is a candidate it is a '
        + 'tentative statement with no status; if it is a node it is a claim with one.')));
  }

  page.appendChild(el('h2', { text: 'How it relates to other routes' }));
  const relations = [];
  if (route.parent) relations.push(el('dt', { text: 'grew out of' }), el('dd', {}, idLink(route.parent)));
  if (route.children.length) relations.push(el('dt', { text: 'grew into' }), el('dd', {}, idList(route.children)));
  for (const relation of route.related) {
    relations.push(el('dt', { text: relation.relation }), el('dd', {}, idLink(relation.to)));
  }
  page.appendChild(relations.length
    ? el('div', { class: 'card' }, el('dl', { class: 'kv' }, relations))
    : emptyState('No recorded relation to another route.'));

  page.appendChild(el('h2', { text: 'Why its state changed' }));
  if (route.checkpoints.length) {
    page.appendChild(el('ul', { class: 'rows' }, route.checkpoints.map((path) =>
      checkpointRow(DATA.memory.checkpoints.find((record) => record.path === path)
        || { path, date: null, outcome: null, nodes: [], superseded_by: [] }))));
  } else {
    page.appendChild(emptyState(
      'No checkpoint is attached. A route that stops owes one; a live route need not.'));
  }

  if (repoBase()) {
    page.appendChild(el('h2', { text: 'Contribute to this route' }));
    page.appendChild(el('div', { class: 'actions' },
      contribute('route-proposal.yml', 'Propose a way past this', route.id),
      contribute('literature-lead.yml', 'Point at existing work', route.id),
      discussLink('Discuss this route')));
  }
  return page;
}

/* -------------------------------------------------------------------- evidence ----- */

function checkpointRow(record) {
  if (!record) return null;
  const superseded = record.superseded_by && record.superseded_by.length;
  return el('li', {},
    el('div', { class: 'row-head' },
      el('span', { class: 'note', text: record.date || '—' }),
      record.outcome
        ? el('span', { class: 'badge neutral', text: OUTCOME_WORD[record.outcome] || record.outcome })
        : null,
      superseded ? el('span', { class: 'badge warn' }, 'superseded') : null,
      fileLink(record.path, null, record.path.split('/').pop()),
      record.approach ? idLink(record.approach) : null),
    record.excerpt ? el('p', { class: 'row-body' }, math(record.excerpt)) : null,
    record.nodes && record.nodes.length
      ? el('p', { class: 'row-note' }, 'engaged ', idList(record.nodes)) : null,
    superseded
      ? el('p', { class: 'row-note' }, 'Read instead: ',
        el('ul', { class: 'inline-list' }, record.superseded_by.map((path) =>
          el('li', {}, fileLink(path, null, path.split('/').pop())))))
      : null);
}

function viewEvidence() {
  const page = el('div', {});
  page.appendChild(el('h1', { text: 'Durable evidence' }));
  page.appendChild(el('p', { class: 'lede' },
    'Why the search is where it is. These records are append-only: nothing here is '
    + 'rewritten or deleted, and a later record may declare an earlier one superseded — '
    + 'which changes what to read first and nothing else.'));

  /* --- candidates ----------------------------------------------------------------- */

  page.appendChild(el('h2', { text: 'Live candidate statements' }));
  page.appendChild(el('p', { class: 'note' },
    'A candidate is a statement somebody thought worth writing down and nothing more. '
    + 'It has no manuscript anchor, no status and no certification, and it is not a '
    + 'claim. Unlike a ledger node’s one-line gloss, a candidate’s text below '
    + 'is canonical — nothing else in the repository holds it.'));
  const candidates = DATA.memory.candidates;
  page.appendChild(candidates.length
    ? el('ul', { class: 'rows' }, candidates.map((candidate) => el('li', {},
      el('div', { class: 'row-head' },
        el('code', { class: 'id', text: candidate.id }),
        el('span', { class: 'badge neutral', text: 'candidate — not a claim' }),
        el('span', { class: 'note', text: candidate.date || '' })),
      el('p', { class: 'row-body gloss' }, math(candidate.statement)),
      el('p', { class: 'row-note' }, 'proposed in ', fileLink(candidate.source)),
      candidate.blocks_routes && candidate.blocks_routes.length
        ? el('p', { class: 'row-note' }, 'blocks ', idList(candidate.blocks_routes)) : null)))
    : emptyState('No live candidates.'));

  const promoted = Object.entries(DATA.memory.promoted);
  if (promoted.length) {
    page.appendChild(el('h3', { text: 'Promoted — no longer candidates' }));
    page.appendChild(el('ul', { class: 'rows' }, promoted.map(([id, promotion]) =>
      el('li', { class: 'tight' }, el('div', { class: 'row-head' },
        el('code', { class: 'id', text: id }), '→', idLink(promotion.node),
        el('span', { class: 'note', text: promotion.date || '' }))))));
  }

  /* --- checkpoints ----------------------------------------------------------------- */

  const heads = DATA.memory.checkpoints.filter((record) => !record.superseded_by.length);
  const stale = DATA.memory.checkpoints.filter((record) => record.superseded_by.length);
  page.appendChild(el('h2', {},
    `Checkpoints — ${heads.length} current`,
    stale.length ? `, ${stale.length} superseded` : ''));
  page.appendChild(heads.length
    ? el('ul', { class: 'rows' }, heads.map(checkpointRow))
    : emptyState('No checkpoints recorded.'));
  if (stale.length) {
    page.appendChild(el('h3', { text: 'Superseded' }));
    page.appendChild(el('ul', { class: 'rows' }, stale.map(checkpointRow)));
  }

  /* --- reviews --------------------------------------------------------------------- */

  const reviews = Object.values(DATA.memory.reviews);
  page.appendChild(el('h2', { text: 'Independent certifications' }));
  page.appendChild(el('p', { class: 'note' },
    'An author never certifies their own proof. Each report below names distinct '
    + 'author(s) and reviewer, and the ledger record that cites it is what makes the '
    + 'node proved.'));
  page.appendChild(reviews.length
    ? el('ul', { class: 'rows' }, reviews.map((review) => el('li', {},
      el('div', { class: 'row-head' },
        el('span', { class: 'note', text: review.date || '—' }),
        el('span', { class: 'badge proved' },
          el('span', { class: 'glyph', 'aria-hidden': 'true', text: '✓' }), review.verdict || '—'),
        fileLink(review.path, null, review.path.split('/').pop())),
      el('dl', { class: 'kv' },
        el('dt', { text: 'reviewer' }), el('dd', { text: review.reviewer || '—' }),
        el('dt', { text: 'author(s)' }), el('dd', { text: review.authors.join(', ') || '—' }),
        el('dt', { text: 'nodes' }), el('dd', {}, idList(review.nodes)),
        el('dt', { text: 'dossiers' }), el('dd', {}, review.solutions.map((path) =>
          el('span', {}, fileLink(path), ' ')))))))
    : emptyState('No certifications recorded.'));

  /* --- audits ---------------------------------------------------------------------- */

  const audits = Object.values(DATA.memory.audits);
  if (audits.length) {
    page.appendChild(el('h2', { text: 'Audits' }));
    page.appendChild(el('p', { class: 'note' },
      'An audit certifies nothing. It reports on the repository itself, and a later '
      + 'audit may supersede it.'));
    page.appendChild(el('ul', { class: 'rows' }, audits.map((audit) => el('li', {},
      el('div', { class: 'row-head' },
        el('span', { class: 'note', text: audit.date || '—' }),
        audit.superseded ? el('span', { class: 'badge warn' }, 'superseded') : null,
        fileLink(audit.path, null, audit.path.split('/').pop())),
      audit.excerpt ? el('p', { class: 'row-body' }, math(audit.excerpt)) : null))));
  }

  /* --- runs ------------------------------------------------------------------------ */

  const runs = DATA.memory.runs;
  page.appendChild(el('h2', { text: 'Numerical run artifacts' }));
  page.appendChild(el('p', { class: 'note' },
    'Provenance-stamped and immutable, and they certify nothing: no run changes a '
    + 'claim, a proof step, or a status. An exact witness a run emits is a candidate '
    + 'until it is checked independently.'));
  page.appendChild(runs.length
    ? el('ul', { class: 'rows' }, runs.map((run) => el('li', { class: 'tight' },
      el('div', { class: 'row-head' },
        fileLink(run.path, null, run.path.split('/').pop()),
        el('span', { class: 'badge neutral', text: `target: ${run.target}` }),
        el('span', { class: 'note', text: `${run.observations} observation(s)` })))))
    : emptyState('No run artifacts.'));

  return page;
}

/* ------------------------------------------------------------------------ router ---- */

const ROUTES = [
  [/^\/?$/, viewTarget, 'target'],
  [/^\/claims\/?$/, viewClaims, 'claims'],
  [/^\/search\/?$/, viewSearch, 'search'],
  [/^\/evidence\/?$/, viewEvidence, 'evidence'],
  [/^\/node\/(.+)$/, viewNode, 'claims'],
  [/^\/route\/(.+)$/, viewRoute, 'search'],
];

function render() {
  const main = document.getElementById('main');
  const path = decodeURIComponent(location.hash.replace(/^#/, '')) || '/';
  let page = null;
  let tab = 'target';
  for (const [pattern, view, name] of ROUTES) {
    const match = pattern.exec(path);
    if (match) { page = view(match[1]); tab = name; break; }
  }
  if (!page) {
    page = el('div', {},
      el('h1', { text: 'Not found' }),
      el('p', { class: 'lede' }, 'Nothing is published at ',
        el('code', { class: 'id', text: path }), '.'),
      el('div', { class: 'actions' }, el('a', { class: 'action', href: '#/' }, 'The target')));
  }
  clear(main);
  main.appendChild(page);
  for (const link of document.querySelectorAll('.tabs a')) {
    if (link.dataset.tab === tab) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
  window.scrollTo(0, 0);
  typeset(main);
}

function chrome() {
  const program = DATA.program;
  const generated = DATA.generated;
  document.getElementById('brand-name').textContent = program.id || 'Conjecture search';
  document.getElementById('brand-sub').textContent = program.target
    ? `target: ${program.target}`
    : 'no target yet — uninstantiated template';
  document.title = program.id ? `${program.id} — conjecture search` : 'Conjecture search';

  const build = document.getElementById('build-provenance');
  const parts = [];
  parts.push(`built ${generated.built_at}`);
  if (generated.short_commit) {
    const link = repoBase()
      ? `${repoBase()}/commit/${generated.commit}` : null;
    parts.push('from ');
    build.appendChild(document.createTextNode(parts.join('')));
    build.appendChild(link
      ? el('a', { href: link, rel: 'noopener', target: '_blank', text: generated.short_commit })
      : document.createTextNode(generated.short_commit));
    if (generated.branch) build.appendChild(document.createTextNode(` on ${generated.branch}`));
  } else {
    build.appendChild(document.createTextNode(`${parts.join('')} from an unknown revision`));
  }
  if (generated.dirty) {
    build.appendChild(el('span', { class: 'dirty',
      text: ' · built from a dirty working tree, not a committed revision' }));
  }
}

fetch('data.json', { cache: 'no-cache' })
  .then((response) => {
    if (!response.ok) throw new Error(`data.json: ${response.status}`);
    return response.json();
  })
  .then((data) => {
    DATA = data;
    chrome();
    window.addEventListener('hashchange', render);
    render();
  })
  .catch((error) => {
    document.getElementById('main').appendChild(el('div', {},
      el('h1', { text: 'This site has no data' }),
      el('p', { class: 'lede' },
        'data.json could not be loaded, so nothing is being displayed. Showing an empty '
        + 'or stale page as though it were the current research state would be worse '
        + 'than showing this one.'),
      el('p', { class: 'note', text: String(error) })));
  });
