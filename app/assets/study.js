/* The Abrahamic Archive — the study layer.
   Choosing verses, highlighting them, writing notes on them, and remembering
   where you were. Vanilla JS, no libraries.

   Everything here is yours and stays in this browser. There are no accounts
   and nothing is sent anywhere: a highlight is a row in localStorage on the
   machine you made it on. That is the whole bargain, and `me.php` will hand
   it all back to you as a file whenever you want it. */
(function () {
  'use strict';

  /* ---------- storage ---------- */
  var DB = {
    read: function (k, d) {
      try { return JSON.parse(localStorage.getItem('aa.' + k)) || d; }
      catch (e) { return d; }
    },
    write: function (k, v) {
      try { localStorage.setItem('aa.' + k, JSON.stringify(v)); return true; }
      catch (e) { return false; }        /* private mode, or the quota */
    }
  };

  /* A verse is keyed by the work, the chapter and its own number. Nothing
     about the key depends on the text, so it survives the corpus being
     rebuilt underneath it — which it has been, many times. */
  function key(work, c, v) { return work + '|' + c + '|' + v; }

  var highlights = DB.read('hl', {});
  var notes      = DB.read('notes', []);

  function noteAt(k) {
    for (var i = 0; i < notes.length; i++) if (notes[i].k === k) return notes[i];
    return null;
  }

  /* ---------- where you were ---------- */
  var reader = document.querySelector('[data-reader]');

  function remember() {
    if (!reader) return;
    var hist = DB.read('hist', []);
    var here = {
      work:  reader.dataset.work,
      c:     reader.dataset.c,
      label: reader.dataset.title + ' ' + reader.dataset.c,
      r:     reader.dataset.religion,
      url:   'read.php?work=' + encodeURIComponent(reader.dataset.work)
             + '&c=' + encodeURIComponent(reader.dataset.c),
      at:    Date.now()
    };
    hist = hist.filter(function (h) { return h.url !== here.url; });
    hist.unshift(here);
    DB.write('hist', hist.slice(0, 40));

    /* Where you were in *this* work, so a work page can offer to resume. */
    var places = DB.read('place', {});
    places[here.work] = { c: here.c, at: here.at, label: here.label };
    DB.write('place', places);
  }
  remember();

  if (!reader || reader.dataset.verses !== '1') { paintLists(); return; }

  /* ---------- choosing verses ---------- */
  var bar     = document.querySelector('[data-vbar]');
  var refOut  = document.querySelector('[data-vbar-ref]');
  var form    = document.querySelector('[data-note-form]');
  var area    = form ? form.querySelector('textarea') : null;
  var chosen  = [];

  /* Verse works are marked up as `.v`; prose works as `.pb`, one paragraph
     at a time. Both carry the same three data attributes, so everything
     downstream — highlighting, notes, copying — is the same code. */
  var UNIT = '.scripture .v, .scripture .pb';

  function verses() {
    return Array.prototype.slice.call(document.querySelectorAll(UNIT));
  }

  function keyOf(el) { return key(el.dataset.work, el.dataset.c, el.dataset.v); }

  function label() {
    if (!chosen.length) return '';
    var first = chosen[0].dataset.ref || '';
    if (chosen.length === 1) return first;
    return first + '–' + chosen[chosen.length - 1].dataset.v;
  }

  function drawBar() {
    if (!bar) return;
    if (!chosen.length) {
      bar.hidden = true;
      if (form) form.hidden = true;
      return;
    }
    bar.hidden = false;
    if (refOut) refOut.textContent = label();
    /* A single verse that already carries a note opens the note ready to edit. */
    var only = chosen.length === 1 ? noteAt(keyOf(chosen[0])) : null;
    if (area && form.hidden) area.value = only ? only.text : '';
    var del = form && form.querySelector('[data-note-delete]');
    if (del) del.hidden = !only;
  }

  /* A chosen verse lights its note in the margin, so the pair read as one
     thing rather than two that happen to be level. */
  function lightNotes() {
    var ids = chosen.map(function (el) { return el.id; });
    document.querySelectorAll('.mnote').forEach(function (n) {
      n.classList.toggle('is-lit', ids.indexOf(n.dataset.for) !== -1);
    });
  }

  function clearChoice() {
    chosen.forEach(function (el) { el.classList.remove('sel'); });
    chosen = [];
    lightNotes();
    drawBar();
  }

  function choose(el, extend) {
    var all = verses();
    if (extend && chosen.length) {
      var a = all.indexOf(chosen[0]);
      var b = all.indexOf(el);
      if (a > b) { var t = a; a = b; b = t; }
      chosen.forEach(function (x) { x.classList.remove('sel'); });
      chosen = all.slice(a, b + 1);
    } else if (chosen.indexOf(el) !== -1) {
      el.classList.remove('sel');
      chosen = chosen.filter(function (x) { return x !== el; });
      lightNotes();
      drawBar();
      return;
    } else {
      chosen.push(el);
    }
    chosen.forEach(function (x) { x.classList.add('sel'); });
    lightNotes();
    drawBar();
  }

  document.addEventListener('click', function (ev) {
    if (ev.target.closest('.vbar')) return;          /* the bar is not the text */
    var v = ev.target.closest(UNIT);
    if (!v) {
      if (chosen.length && !ev.target.closest('a, button')) clearChoice();
      return;
    }
    if (ev.target.closest('.vn')) return;            /* the number still copies */
    choose(v, ev.shiftKey);
  });

  /* ---------- painting what is saved ---------- */
  function paintVerses() {
    verses().forEach(function (el) {
      var k = el.dataset.hlKey || (el.dataset.hlKey = keyOf(el));
      var colour = highlights[k];
      el.className = el.className.replace(/\bhl-\S+/g, '').trim();
      if (colour) el.classList.add('hl-' + colour);
      el.classList.toggle('has-note', !!noteAt(k));
    });
    paintNoteList();
  }

  /* ---------- the margins ----------
     Every note, the translator's and the reader's, is a `.mnote` in one of
     the two `.margin` columns, carrying `data-for` — the id of the verse it
     belongs to. Placing them is then one job done in one place: measure the
     anchor, put the note level with it, and push any note that would land on
     top of the one above it far enough down to clear.

     Nothing here runs below the breakpoint. There the notes stay in the
     ordinary flow under the text, which is what the markup does on its own. */
  var body = document.querySelector('[data-body]');
  var wide = window.matchMedia('(min-width: 68rem)');

  function anchorTop(el, note) {
    var id = note.dataset.for;
    var to = id && document.getElementById(id);
    if (!to) return null;
    return to.getBoundingClientRect().top - el.getBoundingClientRect().top;
  }

  function layout() {
    if (!body) return;
    var margins = body.querySelectorAll('.margin');
    if (!wide.matches) {
      body.classList.remove('pinned');
      margins.forEach(function (m) {
        m.querySelectorAll('.mnote').forEach(function (n) { n.style.top = ''; });
        m.style.minHeight = '';
      });
      return;
    }
    body.classList.add('pinned');
    margins.forEach(function (m) {
      /* The heading sits above everything; notes start below it. */
      var head = m.querySelector('.margin-h');
      var floor = head ? head.offsetHeight + 8 : 0;
      var tallest = floor;
      m.querySelectorAll('.mnote').forEach(function (n) {
        var top = anchorTop(m, n);
        if (top === null) { n.hidden = true; return; }
        n.hidden = false;
        if (top < floor) top = floor;
        n.style.top = Math.round(top) + 'px';
        floor = top + n.offsetHeight + 14;   /* 14px of air between notes */
        tallest = Math.max(tallest, floor);
      });
      m.style.minHeight = tallest + 'px';
    });
  }

  var pending = null;
  function relayout() {
    if (pending) cancelAnimationFrame(pending);
    pending = requestAnimationFrame(function () { pending = null; layout(); });
  }

  window.addEventListener('resize', relayout);
  if (wide.addEventListener) wide.addEventListener('change', relayout);
  /* The reader can change the type size and turn on flowing text, both of
     which move every verse. Watching the column itself catches both without
     study.js having to know anything about the controls that did it. */
  if (window.ResizeObserver) {
    var ro = new ResizeObserver(relayout);
    var col = document.querySelector('.scripture');
    if (col) ro.observe(col);
  }
  document.fonts && document.fonts.ready && document.fonts.ready.then(relayout);

  function paintNoteList() {
    var box = document.querySelector('[data-margin="mine"]');
    if (!box) return;
    var here = notes.filter(function (n) {
      return n.work === reader.dataset.work && String(n.c) === String(reader.dataset.c);
    });
    box.querySelectorAll('.mnote').forEach(function (n) { n.remove(); });
    here.sort(function (a, b) {
      var av = String(a.v), bv = String(b.v);
      return (parseInt(av.replace(/\D/g, ''), 10) || 0)
           - (parseInt(bv.replace(/\D/g, ''), 10) || 0);
    }).forEach(function (n) {
      var el = document.createElement('div');
      el.className = 'mnote mine';
      el.dataset.for = String(n.v).charAt(0) === 'p'
        ? n.v : 'v' + String(n.v).replace(/[^0-9a-z]/gi, '');
      var b = document.createElement('b');
      var a = document.createElement('a');
      a.href = '#' + el.dataset.for;
      a.textContent = n.ref;
      b.appendChild(a);
      var t = document.createElement('span');
      t.className = 'mnote-text';
      t.textContent = n.text;
      el.appendChild(b); el.appendChild(t);
      box.appendChild(el);
    });
    box.hidden = here.length === 0;
    relayout();
  }

  /* ---------- the actions ---------- */
  function setHighlight(colour) {
    chosen.forEach(function (el) {
      var k = keyOf(el);
      if (colour) highlights[k] = colour; else delete highlights[k];
    });
    DB.write('hl', highlights);
    paintVerses();
  }

  function chosenText() {
    return chosen.map(function (el) {
      var body = el.classList.contains('pb')
        ? el.textContent.trim()
        : el.textContent.replace(/^\s*\S+\s*/, '').trim();
      return (el.classList.contains('pb') ? '' : el.dataset.v + ' ') + body;
    }).join(' ');
  }

  function flash(btn, word) {
    var old = btn.textContent;
    btn.textContent = word;
    setTimeout(function () { btn.textContent = old; }, 900);
  }

  if (bar) {
    bar.addEventListener('click', function (ev) {
      var sw = ev.target.closest('[data-hl]');
      if (sw) { setHighlight(sw.dataset.hl); return; }

      var btn = ev.target.closest('[data-act]');
      if (!btn || !chosen.length) return;
      var act = btn.dataset.act;

      if (act === 'close') { clearChoice(); return; }

      if (act === 'compare') {
        location.href = btn.dataset.href + '#' + chosen[0].id;
        return;
      }

      if (act === 'note') {
        form.hidden = !form.hidden;
        if (!form.hidden && area) area.focus();
        return;
      }

      if (act === 'copy' || act === 'share') {
        var url = location.origin + location.pathname + location.search
                + '#' + chosen[0].id;
        var payload = act === 'share'
          ? label() + ' — ' + url
          : label() + ' — ' + chosenText();
        if (navigator.clipboard) {
          navigator.clipboard.writeText(payload).then(function () {
            flash(btn, 'Copied');
          }, function () { flash(btn, 'Blocked'); });
        }
        history.replaceState(null, '', '#' + chosen[0].id);
      }
    });
  }

  if (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!chosen.length) return;
      var el = chosen[0];
      var k  = keyOf(el);
      var text = (area.value || '').trim();
      notes = notes.filter(function (n) { return n.k !== k; });
      if (text) {
        notes.unshift({
          k: k, work: el.dataset.work, c: el.dataset.c, v: el.dataset.v,
          ref: el.dataset.ref, title: reader.dataset.title,
          text: text.slice(0, 4000), at: Date.now()
        });
      }
      DB.write('notes', notes);
      form.hidden = true;
      paintVerses();
      clearChoice();
    });

    form.addEventListener('click', function (ev) {
      if (ev.target.closest('[data-note-cancel]')) { form.hidden = true; }
      if (ev.target.closest('[data-note-delete]') && chosen.length) {
        var k = keyOf(chosen[0]);
        notes = notes.filter(function (n) { return n.k !== k; });
        DB.write('notes', notes);
        form.hidden = true;
        paintVerses();
        clearChoice();
      }
    });
  }

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && chosen.length) clearChoice();
  });

  paintVerses();

  /* ---------- lists rendered on other pages ---------- */
  function paintLists() {
    var cont = document.querySelector('[data-continue]');
    if (cont) {
      var hist = DB.read('hist', []);
      if (!hist.length) { cont.remove(); } else {
        var wrap = cont.querySelector('[data-continue-list]');
        hist.slice(0, 4).forEach(function (h) {
          var a = document.createElement('a');
          a.className = 'work-card';
          a.href = h.url;
          if (h.r) a.setAttribute('data-r', h.r);
          var b = document.createElement('b'); b.textContent = h.label;
          var s = document.createElement('small'); s.textContent = 'Where you left off';
          a.appendChild(b); a.appendChild(s);
          wrap.appendChild(a);
        });
        cont.hidden = false;
      }
    }
  }
  paintLists();
})();
