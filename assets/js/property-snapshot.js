/* ==========================================================================
   property-snapshot.js — ByteMind Property Intelligence landing hydration
   --------------------------------------------------------------------------
   Implements the landing-page hydration contract (publish/CONTRACT.md §5)
   and the iframe embed contract (§6) for the ByteMind site.

   Usage:
     <script src="assets/js/property-snapshot.js"
             data-snapshot="property-scout/data/snapshot.json"
             data-app="property-scout/" defer></script>

   The ZH page points data-snapshot/data-app at "../property-scout/...".

   Everything is progressive: the HTML ships with em dashes and static,
   SEO-readable prose. If the snapshot cannot be fetched, the dashes stay and
   an "snapshot unavailable" note appears — the page never looks broken.
   Vanilla JS only; no dependencies.
   ========================================================================== */
(function () {
  'use strict';

  var script = document.currentScript ||
    document.querySelector('script[data-snapshot]');
  var SNAPSHOT_URL = (script && script.getAttribute('data-snapshot')) ||
    'property-scout/data/snapshot.json';
  var APP_BASE = (script && script.getAttribute('data-app')) ||
    'property-scout/';

  var IS_ZH = (document.documentElement.lang || '').toLowerCase().indexOf('zh') === 0;
  var CURRENCY_PREFIX = IS_ZH ? 'NZ$' : '$';
  var intFormat;
  try {
    intFormat = new Intl.NumberFormat(IS_ZH ? 'zh-CN' : 'en-NZ');
  } catch (e) {
    intFormat = { format: function (n) { return String(n); } };
  }

  var FORMATS = {
    text: function (v) { return String(v); },
    int: function (v) { return intFormat.format(Math.round(Number(v))); },
    number: function (v) { return trimNumber(Number(v), 2); },
    'number1': function (v) { return trimNumber(Number(v), 1); },
    'number2': function (v) { return trimNumber(Number(v), 2); },
    ratio: function (v) { return Number(v).toFixed(2); },
    currency: function (v) { return CURRENCY_PREFIX + compactMillions(Number(v)); },
    'currency-full': function (v) {
      return CURRENCY_PREFIX + intFormat.format(Math.round(Number(v)));
    },
    percent: function (v) { return trimNumber(Number(v), 1) + '%'; },
    'percent2': function (v) { return trimNumber(Number(v), 2) + '%'; },
    'fraction-pct': function (v) { return trimNumber(Number(v) * 100, 1) + '%'; },
    'fraction-pct2': function (v) { return trimNumber(Number(v) * 100, 2) + '%'; },
    'signed-fraction-pct': function (v) {
      var n = Number(v) * 100;
      var sign = n > 0 ? '+' : (n < 0 ? '\u2212' : '');
      return sign + trimNumber(Math.abs(n), 1) + '%';
    },
    'trend-dir': function (v) { return Number(v) > 0 ? 'up' : (Number(v) < 0 ? 'down' : 'flat'); }
  };

  function trimNumber(n, dp) {
    if (!isFinite(n)) return '\u2014';
    var s = n.toFixed(dp);
    return s.replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1');
  }

  function compactMillions(n) {
    if (!isFinite(n)) return '\u2014';
    var abs = Math.abs(n);
    if (abs >= 1000000000) return trimNumber(n / 1000000000, 2) + 'B';
    if (abs >= 1000000) return trimNumber(n / 1000000, 2) + 'M';
    if (abs >= 1000) return trimNumber(n / 1000, 0) + 'k';
    return intFormat.format(n);
  }

  /* Dotted-path lookup that also accepts numeric array indices. */
  function get(obj, path) {
    if (!obj || !path) return undefined;
    var parts = String(path).split('.');
    var cur = obj;
    for (var i = 0; i < parts.length; i++) {
      if (cur == null) return undefined;
      cur = cur[parts[i]];
    }
    return cur;
  }

  function formatValue(value, format) {
    if (value === null || value === undefined || value === '') return null;
    var fn = FORMATS[format] || FORMATS.text;
    try {
      return fn(value);
    } catch (e) {
      return null;
    }
  }

  /* ── [data-snap] scalar hooks ──────────────────────────────────── */
  function hydrateScalars(root, snapshot) {
    var nodes = root.querySelectorAll('[data-snap]');
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var path = el.getAttribute('data-snap');
      var value = get(snapshot, path);
      var formatted = formatValue(value, el.getAttribute('data-format') || 'text');
      if (formatted !== null) {
        el.textContent = formatted;
        el.removeAttribute('data-snap-missing');
        if (value === null || value === undefined) {
          el.setAttribute('data-snap-missing', '');
        }
      }
    }
  }

  /* ── [data-snap-list] template lists (suburbs, sale methods) ───── */
  function hydrateList(name, snapshot, decorateRow) {
    var container = document.querySelector('[data-snap-list="' + name + '"]');
    if (!container) return;
    var template = container.querySelector('template[data-row]');
    var items = get(snapshot, name);
    if (!template || !Array.isArray(items)) return;

    var empty = container.querySelectorAll('[data-empty]');
    for (var e = 0; e < empty.length; e++) {
      empty[e].hidden = items.length > 0;
    }
    if (!items.length) return;

    var fragment = document.createDocumentFragment();
    items.forEach(function (item) {
      var row = template.content.cloneNode(true);
      var fields = row.querySelectorAll('[data-field]');
      for (var j = 0; j < fields.length; j++) {
        var field = fields[j];
        var key = field.getAttribute('data-field');
        var formatted = formatValue(get(item, key),
          field.getAttribute('data-format') || 'text');
        if (formatted !== null) field.textContent = formatted;
      }
      if (typeof decorateRow === 'function') decorateRow(row, item);
      fragment.appendChild(row);
    });
    container.appendChild(fragment);
  }

  function renderSuburbs(snapshot) {
    hydrateList('suburbs', snapshot, function (row, item) {
      var cell = row.querySelector('[data-field="trend_12w"]');
      if (!cell) return;
      var v = Number(item.trend_12w);
      if (!isFinite(v)) return;
      cell.classList.add(v > 0 ? 'pi-trend-up' : (v < 0 ? 'pi-trend-down' : 'pi-trend-flat'));
    });
  }

  function renderSaleMethods(snapshot) {
    var container = document.querySelector('[data-snap-list="sale_methods"]');
    if (!container) return;
    var items = get(snapshot, 'sale_methods');
    if (!Array.isArray(items) || !items.length) return;
    var max = 0;
    items.forEach(function (m) { max = Math.max(max, Number(m.share_pct) || 0); });

    hydrateList('sale_methods', snapshot, function (row, item) {
      var fill = row.querySelector('.pi-bar-fill');
      if (!fill) return;
      var share = Number(item.share_pct) || 0;
      var width = max > 0 ? Math.max(3, Math.min(100, (share / max) * 100)) : 0;
      // Set after insertion so the width transition runs instead of snapping.
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { fill.style.width = width.toFixed(1) + '%'; });
      });
    });
  }

  /* ── 12-week trend sparkline ───────────────────────────────────── */
  function renderSpark(snapshot) {
    var target = document.querySelector('[data-spark="trend"]');
    if (!target) return;
    var series = get(snapshot, 'trend.series');
    var points = [];
    if (Array.isArray(series)) {
      series.forEach(function (pt) {
        var v = pt && pt.median_estimate;
        if (typeof v === 'number' && isFinite(v)) {
          points.push({ week: String(pt.week || ''), value: v });
        }
      });
    }

    var startLabel = document.querySelector('[data-spark-start]');
    var endLabel = document.querySelector('[data-spark-end]');
    if (startLabel && points.length) startLabel.textContent = points[0].week;
    if (endLabel && points.length) endLabel.textContent = points[points.length - 1].week;

    if (points.length < 2) {
      var empty = document.querySelector('[data-spark-empty]');
      if (empty) empty.hidden = false;
      return;
    }

    var W = 320, H = 108, PAD = 10;
    var values = points.map(function (p) { return p.value; });
    var min = Math.min.apply(null, values);
    var max = Math.max.apply(null, values);
    var span = max - min || 1;
    var coords = points.map(function (p, idx) {
      var x = PAD + (idx / (points.length - 1)) * (W - PAD * 2);
      var y = H - PAD - ((p.value - min) / span) * (H - PAD * 2);
      return [x, y];
    });

    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('class', 'pi-spark');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label',
      (IS_ZH ? '12 周估值中位数走势图' : '12-week median estimate trend') +
      ': ' + compactMillions(values[0]) + ' \u2192 ' + compactMillions(values[values.length - 1])
    );

    var area = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    area.setAttribute('points', coords.map(function (c) { return c[0] + ',' + c[1]; }).join(' ') +
      ' ' + coords[coords.length - 1][0] + ',' + H + ' ' + coords[0][0] + ',' + H);
    area.setAttribute('fill', 'rgba(26, 58, 42, 0.06)');
    svg.appendChild(area);

    var line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    line.setAttribute('points', coords.map(function (c) { return c[0] + ',' + c[1]; }).join(' '));
    line.setAttribute('fill', 'none');
    line.setAttribute('stroke', '#306d49');
    line.setAttribute('stroke-width', '1.75');
    line.setAttribute('stroke-linecap', 'round');
    line.setAttribute('stroke-linejoin', 'round');
    svg.appendChild(line);

    var last = coords[coords.length - 1];
    var dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    dot.setAttribute('cx', last[0]);
    dot.setAttribute('cy', last[1]);
    dot.setAttribute('r', '2.75');
    dot.setAttribute('fill', '#1a3a2a');
    svg.appendChild(dot);

    target.innerHTML = '';
    target.appendChild(svg);
    target.classList.add('is-rendered');
  }

  /* ── Deep links into the static app ───────────────────────────── */
  function hydrateDeepLinks(snapshot) {
    var top = get(snapshot, 'top_value.0.id');
    var link = document.querySelector('[data-deeplink="property"]');
    if (!link) return;
    if (typeof top === 'string' && /^[A-Za-z0-9_-]+$/.test(top)) {
      link.setAttribute('href', APP_BASE + '#/property/' + top);
      link.removeAttribute('aria-disabled');
    }
  }

  /* ── Embed: desktop iframe only; mobile keeps poster + link ────── */
  function setupEmbed() {
    var map = document.querySelector('[data-pi-map]');
    if (!map) return;

    var poster = map.querySelector('[data-pi-poster]');
    if (poster) {
      function markLoaded() { poster.classList.add('is-loaded'); }
      function dropPoster() { if (poster.parentNode) poster.parentNode.removeChild(poster); }
      poster.addEventListener('load', markLoaded);
      poster.addEventListener('error', dropPoster);
      if (poster.complete && poster.naturalWidth > 0) markLoaded();
    }

    var slot = map.querySelector('[data-pi-embed-slot]');
    var src = map.getAttribute('data-embed-src');
    if (!slot || !src) return;

    var mq;
    try {
      mq = window.matchMedia('(min-width: 900px)');
    } catch (e) {
      return;
    }
    if (!mq.matches) return;

    var frame = document.createElement('iframe');
    frame.src = src;
    frame.title = map.getAttribute('data-embed-title') || 'Auckland Property Scout interactive map';
    frame.loading = 'lazy';
    frame.setAttribute('allow', 'fullscreen');

    // The poster (or the illustration behind it) stays visible until the app
    // has rendered. A slow or missing app degrades to the poster instead of a
    // blank frame or a server directory listing.
    function showFallback(zhText, enText) {
      map.classList.remove('is-ready');
      map.classList.add('is-unavailable');
      var status = map.querySelector('[data-pi-map-status]');
      if (status) status.textContent = IS_ZH ? zhText : enText;
      var note = document.querySelector('[data-pi-map-fallback]');
      if (note) note.hidden = false;
    }

    frame.addEventListener('load', function () {
      // Same-origin: if the static app has not been published yet, the host
      // serves its 404 page or a directory listing inside the frame.
      try {
        var doc = frame.contentDocument;
        var hasApp = !!(doc && (doc.getElementById('root') || doc.querySelector('[data-apr-app]')));
        var looks404 = !!(doc && /page not found|404/i.test(doc.title || ''));
        if (!hasApp || looks404) {
          if (frame.parentNode) frame.parentNode.removeChild(frame);
          showFallback(
            '\u5b9e\u65f6\u5e94\u7528\u5c1a\u672a\u53d1\u5e03\u2014\u2014\u4e0a\u65b9\u622a\u56fe\u4ecd\u53ef\u53c2\u8003\uff0c\u8bf7\u76f4\u63a5\u6253\u5f00\u5e94\u7528\u3002',
            'The live app is not available in this preview \u2014 the screenshot above still applies; open the app directly.');
          return;
        }
      } catch (err) { /* cross-origin: trust the frame */ }
      map.classList.add('is-ready');
    });
    slot.appendChild(frame);

    // If nothing renders within 12s, point the reader at the app while the
    // poster stays on screen. A later apr:ready still promotes the map.
    window.setTimeout(function () {
      if (map.classList.contains('is-ready')) return;
      var note = document.querySelector('[data-pi-map-fallback]');
      if (note) note.hidden = false;
    }, 12000);

    window.addEventListener('message', function (event) {
      if (event.data && event.data.type === 'apr:ready') {
        map.classList.remove('is-unavailable');
        map.classList.add('is-ready');
        var note = document.querySelector('[data-pi-map-fallback]');
        if (note) note.hidden = true;
      }
    });
  }

  function hydrate(snapshot) {
    hydrateScalars(document, snapshot);
    renderSuburbs(snapshot);
    renderSaleMethods(snapshot);
    renderSpark(snapshot);
    hydrateDeepLinks(snapshot);
    document.documentElement.classList.add('snapshot-loaded');
  }

  function markUnavailable(reason) {
    document.documentElement.classList.add('snapshot-unavailable');
    if (window.console && console.warn) {
      console.warn('[property-snapshot] snapshot unavailable: ' + reason);
    }
  }

  function boot() {
    setupEmbed();

    if (!window.fetch) {
      markUnavailable('fetch not supported');
      return;
    }

    // no-store plus a timestamp cache-buster: a new daily snapshot is never
    // served from the browser cache (the generated_at value is only known
    // after the response, so the request carries a fresh token instead).
    fetch(SNAPSHOT_URL + '?v=' + Date.now(), {
      cache: 'no-store',
      credentials: 'same-origin'
    })
      .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      })
      .then(hydrate)
      .catch(function (err) {
        markUnavailable(err && err.message ? err.message : 'fetch failed');
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
