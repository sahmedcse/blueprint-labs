/* Annotation layer for blueprint-labs review pages.
 *
 * `review.sh register` injects this into an artifact with window.BPL = {req, artifact, rev,
 * title, owner, round}. Ported from Profitify's design-gate layer.
 *
 * Toggle "Annotate" and click anything to pin a numbered note. Notes persist in localStorage per
 * artifact and revision, and autosave to the review server. "Send notes: revise" goes to the
 * agent that owns this artifact. "Approve" unblocks the work that depends on it. Claude picks up
 * either one without you returning to the terminal.
 *
 * The only requests this script makes go to its own loopback origin.
 */
(function () {
  if (window.__bplAnnotate) return;
  window.__bplAnnotate = true;

  var CFG = window.BPL || {};
  var RUN = CFG.req || 'page';
  var ART = CFG.artifact || 'page';
  // Keyed per artifact and revision so notes from an earlier revision don't reappear.
  var KEY = 'bpl:' + RUN + ':' + ART + ':' + (CFG.rev || '');
  var notes = load();
  var on = false;
  var hoverEl = null;
  // Served by the gate's local server: notes autosave to <run>/notes.json and "Done" hands off.
  var SERVED = location.protocol === 'http:';
  var syncTimer = null;

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { return []; }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(notes)); } catch (e) { /* private window: notes live until reload */ }
    if (SERVED) { clearTimeout(syncTimer); syncTimer = setTimeout(function () { sync(false); }, 600); }
  }
  function sync(done, decision) {
    return fetch('/__notes/' + ART, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rev: CFG.rev || null, done: done, decision: decision || null,
        saved_at: new Date().toISOString(),
        notes: notes.map(function (n) { return { label: n.label, target: n.target, text: n.text }; })
      })
    }).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); });
  }
  function clean(s, n) {
    s = (s || '').replace(/\s+/g, ' ').trim();
    return s.length > n ? s.slice(0, n - 1) + '…' : s;
  }

  // "2 · Loading, empty and error… › Price" — the section heading, then the card title.
  function labelFor(el) {
    var parts = [];
    var sec = el.closest('.section');
    var h = sec && sec.querySelector('h2');
    if (h) parts.push(clean(h.textContent, 60));
    var card = el.closest('section.card, .card');
    if (card) {
      var t = card.querySelector('.ch .t, .lh b, h1, h3');
      if (t) parts.push(clean(t.textContent, 40));
    }
    // Documents without mockup sections (the rendered plan): use the nearest heading above.
    if (!parts.length) {
      var hs = document.querySelectorAll('h1, h2, h3, h4');
      var near = null;
      for (var i = 0; i < hs.length; i++) {
        if (hs[i] === el || hs[i].contains(el) ||
            (hs[i].compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING)) near = hs[i];
      }
      if (near) parts.push(clean(near.textContent, 70));
    }
    return parts.join(' › ') || 'page';
  }

  // ---- styles -------------------------------------------------------------------
  var css = document.createElement('style');
  css.textContent = [
    '.bpl-panel{position:fixed;right:16px;bottom:16px;z-index:2147483000;width:340px;max-width:calc(100vw - 32px);',
    ' max-height:70vh;display:flex;flex-direction:column;background:#111827;color:#f3f4f6;border:1px solid #374151;',
    ' border-radius:12px;box-shadow:0 12px 40px rgba(0,0,0,.35);font:13px/1.45 system-ui,-apple-system,sans-serif}',
    '.bpl-panel.min .bpl-body{display:none}',
    '.bpl-head{display:flex;gap:6px;align-items:center;padding:10px 12px;border-bottom:1px solid #374151}',
    '.bpl-head b{flex:1;font-size:13px}',
    '.bpl-btn{background:#1f2937;color:#f3f4f6;border:1px solid #4b5563;border-radius:7px;padding:5px 9px;',
    ' font:600 12px system-ui,sans-serif;cursor:pointer}',
    '.bpl-btn:hover{border-color:#9ca3af}',
    '.bpl-btn.on{background:#0891b2;border-color:#0891b2;color:#fff}',
    '.bpl-body{overflow:auto;padding:8px 12px 12px}',
    '.bpl-hint{color:#9ca3af;font-size:12px;margin:4px 0 8px}',
    '.bpl-note{border:1px solid #374151;border-radius:8px;padding:8px;margin:0 0 8px}',
    '.bpl-note .lbl{display:flex;gap:6px;align-items:baseline;font-size:11px;color:#9ca3af;margin-bottom:4px}',
    '.bpl-note .lbl span{flex:1}',
    '.bpl-note textarea,.bpl-out{width:100%;box-sizing:border-box;background:#0b1220;color:#f3f4f6;border:1px solid #374151;',
    ' border-radius:6px;padding:6px;font:13px/1.4 system-ui,sans-serif;resize:vertical}',
    '.bpl-note textarea{min-height:52px}',
    '.bpl-x{background:none;border:none;color:#9ca3af;cursor:pointer;font-size:14px;padding:0 2px}',
    '.bpl-x:hover{color:#f87171}',
    '.bpl-foot{display:flex;gap:6px;flex-wrap:wrap;margin-top:4px}',
    '.bpl-out{margin-top:8px;min-height:90px;font:12px/1.4 ui-monospace,Menlo,monospace}',
    '.bpl-pin{position:absolute;z-index:2147482999;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;',
    ' background:#f59e0b;color:#111827;border:2px solid #fff;font:700 11px/18px system-ui,sans-serif;text-align:center;',
    ' box-shadow:0 2px 8px rgba(0,0,0,.35);cursor:pointer}',
    '.bpl-pin.hl{background:#0891b2;color:#fff}',
    'body.bpl-on,body.bpl-on *{cursor:crosshair!important}',
    '.bpl-hover{outline:2px dashed #f59e0b!important;outline-offset:2px}',
    '.bpl-num{display:inline-block;min-width:18px;height:18px;border-radius:50%;background:#f59e0b;color:#111827;',
    ' text-align:center;font:700 11px/18px system-ui,sans-serif}'
  ].join('\n');
  document.head.appendChild(css);

  // ---- panel --------------------------------------------------------------------
  var panel = document.createElement('div');
  panel.className = 'bpl-panel';
  panel.innerHTML =
    '<div class="bpl-head"><a class="bpl-btn" href="/" title="Back to the hub">◂ Hub</a>' +
    '<b>Notes <span id="bpl-count"></span></b>' +
    '<button class="bpl-btn" id="bpl-toggle" type="button">Annotate</button>' +
    '<button class="bpl-btn" id="bpl-min" type="button" title="Minimise">–</button></div>' +
    '<div class="bpl-body">' +
    '<p class="bpl-hint">Turn on <b>Annotate</b>, click anything on the page and type a note ' +
    '(<b>Esc</b> stops annotating). ' +
    (SERVED ? 'Notes save automatically. Click <b>Send notes</b> to have the designer revise, or <b>' + ('Approve') + '</b> ' +
      'to move on. Claude picks either up without you returning to the terminal.</p>'
            : 'When you are done, <b>Copy notes</b> and paste them into the terminal.</p>') +
    '<div id="bpl-list"></div>' +
    '<div class="bpl-foot">' +
    (SERVED ? '<button class="bpl-btn on" id="bpl-done" type="button">Send notes — revise</button>' +
              '<button class="bpl-btn" id="bpl-approve" type="button">' + ('Approve') + '</button>' : '') +
    '<button class="bpl-btn" id="bpl-copy" type="button">Copy notes</button>' +
    '<button class="bpl-btn" id="bpl-clear" type="button">Clear all</button></div>' +
    '<textarea class="bpl-out" id="bpl-out" readonly hidden></textarea></div>';
  document.body.appendChild(panel);

  var $ = function (id) { return document.getElementById(id); };
  var pinLayer = document.createElement('div');
  document.body.appendChild(pinLayer);

  function render() {
    $('bpl-count').textContent = notes.length ? '(' + notes.length + ')' : '';
    var list = $('bpl-list');
    list.innerHTML = '';
    pinLayer.innerHTML = '';
    notes.forEach(function (n, i) {
      var row = document.createElement('div');
      row.className = 'bpl-note';
      row.innerHTML = '<div class="lbl"><span class="bpl-num">' + (i + 1) + '</span><span></span>' +
        '<button class="bpl-x" type="button" title="Delete note">✕</button></div><textarea></textarea>';
      row.querySelector('.lbl span:nth-child(2)').textContent = n.label + (n.target ? ' — “' + n.target + '”' : '');
      var ta = row.querySelector('textarea');
      ta.value = n.text;
      ta.placeholder = 'What should change here?';
      ta.addEventListener('input', function () { n.text = ta.value; save(); });
      row.querySelector('.bpl-x').addEventListener('click', function () {
        notes.splice(i, 1); save(); render();
      });
      list.appendChild(row);

      var pin = document.createElement('div');
      pin.className = 'bpl-pin';
      pin.textContent = i + 1;
      pin.style.left = n.x + 'px';
      pin.style.top = n.y + 'px';
      pin.title = n.text || n.label;
      pin.addEventListener('click', function (e) {
        e.stopPropagation();
        panel.classList.remove('min');
        ta.focus();
        ta.scrollIntoView({ block: 'nearest' });
      });
      pinLayer.appendChild(pin);
    });
  }

  function exportText() {
    var lines = ['Review notes — ' + RUN + ' ' + ART + ' (' + notes.length + ')', ''];
    notes.forEach(function (n, i) {
      lines.push((i + 1) + '. [' + n.label + ']' + (n.target ? ' “' + n.target + '”' : '') + ': ' +
        (clean(n.text, 2000) || '(no text)'));
    });
    return lines.join('\n');
  }

  function copy(text) {
    var out = $('bpl-out');
    out.value = text;
    out.hidden = false;
    var done = function (ok) { $('bpl-copy').textContent = ok ? 'Copied ✓' : 'Select below and copy'; };
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () { fallback(); });
        return;
      }
    } catch (e) { /* fall through */ }
    fallback();
    function fallback() {
      out.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      done(ok);
    }
  }

  function setOn(v) {
    on = v;
    $('bpl-toggle').classList.toggle('on', on);
    $('bpl-toggle').textContent = on ? 'Annotating…' : 'Annotate';
    document.body.classList.toggle('bpl-on', on);
    if (!on && hoverEl) { hoverEl.classList.remove('bpl-hover'); hoverEl = null; }
  }

  $('bpl-toggle').addEventListener('click', function () { setOn(!on); });
  $('bpl-min').addEventListener('click', function () { panel.classList.toggle('min'); });
  $('bpl-copy').addEventListener('click', function () { copy(exportText()); });
  if (SERVED) {
    var decide = function (btn, decision, sentLabel) {
      if (decision === 'revise' && !notes.some(function (n) { return (n.text || '').trim(); })) {
        $(btn).textContent = 'Add a note first';
        return;
      }
      clearTimeout(syncTimer);
      $(btn).textContent = 'Sending…';
      sync(true, decision).then(function () {
        setOn(false);
        $(btn).textContent = sentLabel;
        // Back to the hub, which jumps to the next artifact still waiting on you.
        setTimeout(function () { location.href = '/#next'; }, 1200);
      }, function () {
        $(btn).textContent = 'Could not reach Claude — use Copy notes';
      });
    };
    $('bpl-done').addEventListener('click', function () { decide('bpl-done', 'revise', 'Sent ✓ — ' + (CFG.owner || 'owner') + ' is revising'); });
    $('bpl-approve').addEventListener('click', function () {
      decide('bpl-approve', 'approve', 'Approved ✓ — back to the hub');
    });
  }
  var clearArmed = false;
  $('bpl-clear').addEventListener('click', function () {
    if (!notes.length) return;
    if (!clearArmed) {
      clearArmed = true;
      $('bpl-clear').textContent = 'Click again to clear';
      setTimeout(function () { clearArmed = false; $('bpl-clear').textContent = 'Clear all'; }, 3000);
      return;
    }
    clearArmed = false;
    $('bpl-clear').textContent = 'Clear all';
    notes = []; save(); render();
  });

  document.addEventListener('mouseover', function (e) {
    if (!on || panel.contains(e.target)) return;
    if (hoverEl) hoverEl.classList.remove('bpl-hover');
    hoverEl = e.target;
    hoverEl.classList.add('bpl-hover');
  }, true);

  // Capture phase so the mockup's own buttons (tabs, theme toggle) don't fire while annotating.
  document.addEventListener('click', function (e) {
    if (!on || panel.contains(e.target) || e.target.classList.contains('bpl-pin')) return;
    e.preventDefault();
    e.stopPropagation();
    var el = e.target;
    el.classList.remove('bpl-hover');
    notes.push({
      x: e.pageX, y: e.pageY,
      label: labelFor(el),
      target: clean(el.textContent, 40),
      text: ''
    });
    save();
    panel.classList.remove('min');
    render();
    var tas = $('bpl-list').querySelectorAll('textarea');
    if (tas.length) { tas[tas.length - 1].focus(); tas[tas.length - 1].scrollIntoView({ block: 'nearest' }); }
  }, true);

  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && on) setOn(false); });

  render();
})();
