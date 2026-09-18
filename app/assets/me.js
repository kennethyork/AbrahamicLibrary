/* Reads back everything the study layer saved, and hands it over on request.
   Nothing here talks to the server. */
(function () {
  'use strict';

  function read(k, d) {
    try { return JSON.parse(localStorage.getItem('aa.' + k)) || d; }
    catch (e) { return d; }
  }

  var notes = read('notes', []);
  var hl    = read('hl', {});
  var hist  = read('hist', []);
  var marks = read('bookmarks', []);

  function show(name) {
    var el = document.querySelector('[data-panel="' + name + '"]');
    if (el) el.hidden = false;
  }
  function list(name) { return document.querySelector('[data-list="' + name + '"]'); }
  function count(name, n, word) {
    var el = document.querySelector('[data-count="' + name + '"]');
    if (el) el.textContent = n + ' ' + word + (n === 1 ? '' : 's');
  }

  /* A highlight is stored as `work|chapter|verse`, which is all that is
     needed to find it again and all that is worth keeping. The reference a
     reader recognises is rebuilt from a note on the same verse when there is
     one, and otherwise from the key. */
  function refFor(key) {
    for (var i = 0; i < notes.length; i++) if (notes[i].k === key) return notes[i].ref;
    var bits = key.split('|');
    return bits[1] + ':' + bits[2];
  }
  function urlFor(key) {
    var b = key.split('|');
    var frag = String(b[2]).charAt(0) === 'p'
      ? b[2] : 'v' + String(b[2]).replace(/[^0-9a-z]/gi, '');
    return 'read.php?work=' + encodeURIComponent(b[0]) + '&c='
         + encodeURIComponent(b[1]) + '#' + frag;
  }
  function titleFor(key) {
    var work = key.split('|')[0];
    for (var i = 0; i < notes.length; i++) if (notes[i].work === work) return notes[i].title;
    for (var j = 0; j < hist.length; j++) {
      if (hist[j].work === work) return hist[j].label.replace(/\s+\S+$/, '');
    }
    return work;
  }

  /* ---------- where you were ---------- */
  if (hist.length) {
    show('continue');
    hist.slice(0, 12).forEach(function (h) {
      var a = document.createElement('a');
      a.className = 'work-card';
      a.href = h.url;
      if (h.r) a.setAttribute('data-r', h.r);
      var b = document.createElement('b'); b.textContent = h.label;
      var s = document.createElement('small');
      s.textContent = new Date(h.at).toLocaleDateString();
      a.appendChild(b); a.appendChild(s);
      list('continue').appendChild(a);
    });
  }

  /* ---------- notes ---------- */
  if (notes.length) {
    show('notes');
    count('notes', notes.length, 'note');
    notes.slice().sort(function (a, b) { return b.at - a.at; }).forEach(function (n) {
      var card = document.createElement('article');
      card.className = 'note-card';
      var a = document.createElement('a');
      a.href = urlFor(n.k); a.textContent = n.ref;
      var p = document.createElement('p'); p.textContent = n.text;
      var t = document.createElement('small');
      t.className = 'muted';
      t.textContent = new Date(n.at).toLocaleDateString();
      card.appendChild(a); card.appendChild(p); card.appendChild(t);
      list('notes').appendChild(card);
    });
  }

  /* ---------- highlights, gathered by the work they are in ---------- */
  var keys = Object.keys(hl);
  if (keys.length) {
    show('highlights');
    count('highlights', keys.length, 'verse');
    var byWork = {};
    keys.forEach(function (k) {
      var w = k.split('|')[0];
      (byWork[w] = byWork[w] || []).push(k);
    });
    Object.keys(byWork).forEach(function (w) {
      var h = document.createElement('h3');
      h.className = 'hl-group';
      h.textContent = titleFor(w + '|0|0');
      list('highlights').appendChild(h);
      var row = document.createElement('div');
      row.className = 'hl-row';
      byWork[w].sort(function (a, b) {
        var x = a.split('|'), y = b.split('|');
        return (+x[1] - +y[1]) || (+x[2] - +y[2]);
      }).forEach(function (k) {
        var a = document.createElement('a');
        a.className = 'hl-chip hl-' + hl[k];
        a.href = urlFor(k);
        a.textContent = refFor(k);
        row.appendChild(a);
      });
      list('highlights').appendChild(row);
    });
  }

  if (marks.length) show('bookmarks');
  if (!notes.length && !keys.length && !hist.length && !marks.length) show('empty');

  /* ---------- taking it away, and putting it back ---------- */
  function say(msg) {
    var el = document.querySelector('[data-io-msg]');
    if (el) el.textContent = msg;
  }

  var out = document.querySelector('[data-export]');
  if (out) {
    out.addEventListener('click', function () {
      var payload = {
        archive: 'The Abrahamic Library',
        saved: new Date().toISOString(),
        notes: notes, highlights: hl, history: hist, bookmarks: marks
      };
      var blob = new Blob([JSON.stringify(payload, null, 2)],
                          { type: 'application/json' });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'abrahamic-archive-reading.json';
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 5000);
      say('Downloaded.');
    });
  }

  var inp = document.querySelector('[data-import]');
  if (inp) {
    inp.addEventListener('change', function () {
      var f = inp.files && inp.files[0];
      if (!f) return;
      var fr = new FileReader();
      fr.onload = function () {
        try {
          var d = JSON.parse(fr.result);
          /* Merged, not replaced: restoring a copy from a second device
             should not throw away what was made on this one. */
          var n = read('notes', []).slice();
          (d.notes || []).forEach(function (x) {
            if (!n.some(function (y) { return y.k === x.k; })) n.push(x);
          });
          var h = read('hl', {});
          Object.keys(d.highlights || {}).forEach(function (k) { h[k] = d.highlights[k]; });
          localStorage.setItem('aa.notes', JSON.stringify(n));
          localStorage.setItem('aa.hl', JSON.stringify(h));
          if (d.bookmarks) localStorage.setItem('aa.bookmarks', JSON.stringify(d.bookmarks));
          say('Restored. Reloading…');
          setTimeout(function () { location.reload(); }, 700);
        } catch (e) {
          say('That file could not be read.');
        }
      };
      fr.readAsText(f);
    });
  }
})();
