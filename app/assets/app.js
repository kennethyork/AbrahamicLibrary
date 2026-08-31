/* The Abrahamic Archive — vanilla JS, no libraries.
   Theme, reading preferences, verse anchors and bookmarks.
   Everything stored here is per-reader and lives only in this browser. */
(function () {
  'use strict';

  var store = {
    get: function (k, d) {
      try { var v = localStorage.getItem('aa.' + k); return v === null ? d : v; }
      catch (e) { return d; }
    },
    set: function (k, v) {
      try { localStorage.setItem('aa.' + k, v); } catch (e) { /* private mode */ }
    },
    del: function (k) {
      try { localStorage.removeItem('aa.' + k); } catch (e) { /* ignore */ }
    }
  };

  /* ---------- theme ---------- */
  var root = document.documentElement;
  var saved = store.get('theme', '');
  if (saved === 'dark' || saved === 'light') root.setAttribute('data-theme', saved);

  var toggle = document.querySelector('[data-theme-toggle]');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var now = root.getAttribute('data-theme');
      if (!now) {
        var dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        now = dark ? 'dark' : 'light';
      }
      var next = now === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      store.set('theme', next);
    });
  }

  /* ---------- reading preferences ---------- */
  var scripture = document.querySelector('.scripture');
  if (scripture) {
    var SIZES = ['1rem', '1.08rem', '1.16rem', '1.28rem', '1.42rem', '1.6rem'];
    var size = parseInt(store.get('size', '2'), 10);
    if (isNaN(size) || size < 0 || size >= SIZES.length) size = 2;

    var flowing = store.get('flowing', '0') === '1';

    function apply() {
      scripture.style.setProperty('--read-size', SIZES[size]);
      scripture.classList.toggle('flowing', flowing);
      var fb = document.querySelector('[data-flowing]');
      if (fb) fb.setAttribute('aria-pressed', flowing ? 'true' : 'false');
    }

    document.addEventListener('click', function (ev) {
      var el = ev.target.closest('[data-size]');
      if (el) {
        size = Math.max(0, Math.min(SIZES.length - 1, size + (+el.dataset.size)));
        store.set('size', String(size));
        apply();
        return;
      }
      if (ev.target.closest('[data-flowing]')) {
        flowing = !flowing;
        store.set('flowing', flowing ? '1' : '0');
        apply();
      }
    });

    apply();
  }

  /* ---------- verse anchors ---------- */
  function markTarget() {
    document.querySelectorAll('.v.target').forEach(function (el) {
      el.classList.remove('target');
    });
    if (!location.hash) return;
    var el = document.getElementById(location.hash.slice(1));
    if (el) el.classList.add('target');
  }
  window.addEventListener('hashchange', markTarget);
  markTarget();

  /* copy a verse reference by clicking its number */
  document.addEventListener('click', function (ev) {
    var vn = ev.target.closest('.vn');
    if (!vn || !navigator.clipboard) return;
    var verse = vn.closest('.v');
    if (!verse) return;
    ev.preventDefault();
    var ref = vn.dataset.ref || '';
    var text = verse.textContent.replace(/^\s*\d+\s*/, '').trim();
    navigator.clipboard.writeText(ref ? ref + ' — ' + text : text).then(function () {
      var old = vn.textContent;
      vn.textContent = '✓';
      setTimeout(function () { vn.textContent = old; }, 800);
    }, function () { /* clipboard refused */ });
    history.replaceState(null, '', '#' + verse.id);
    markTarget();
  });

  /* ---------- bookmarks ---------- */
  var BOOKMARKS = 'bookmarks';

  function bookmarks() {
    try { return JSON.parse(store.get(BOOKMARKS, '[]')) || []; }
    catch (e) { return []; }
  }

  function saveBookmarks(list) {
    store.set(BOOKMARKS, JSON.stringify(list.slice(0, 200)));
  }

  var markBtn = document.querySelector('[data-bookmark]');
  if (markBtn) {
    var here = {
      url: location.pathname.split('/').pop() + location.search,
      label: markBtn.dataset.bookmark
    };

    function isMarked() {
      return bookmarks().some(function (b) { return b.url === here.url; });
    }

    function paint() {
      var on = isMarked();
      markBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
      markBtn.textContent = on ? 'Bookmarked' : 'Bookmark';
    }

    markBtn.addEventListener('click', function () {
      var list = bookmarks().filter(function (b) { return b.url !== here.url; });
      if (!isMarked()) list.unshift(here);
      saveBookmarks(list);
      paint();
    });

    paint();
  }

  var shelf = document.querySelector('[data-bookmark-list]');
  if (shelf) {
    var list = bookmarks();
    if (!list.length) {
      shelf.innerHTML = '<p class="muted small">No bookmarks yet. Open any '
        + 'chapter and choose <em>Bookmark</em> to keep your place here.</p>';
    } else {
      var ul = document.createElement('div');
      ul.className = 'grid-works';
      list.forEach(function (b) {
        var a = document.createElement('a');
        a.className = 'work-card';
        a.href = b.url;
        a.innerHTML = '<b></b><small>Saved on this device</small>';
        a.querySelector('b').textContent = b.label;
        ul.appendChild(a);
      });
      shelf.appendChild(ul);
    }
  }

  /* ---------- keyboard ---------- */
  document.addEventListener('keydown', function (ev) {
    if (ev.altKey || ev.ctrlKey || ev.metaKey) return;
    var tag = (ev.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

    if (ev.key === '/') {
      var q = document.getElementById('q');
      if (q) { ev.preventDefault(); q.focus(); q.select(); }
      return;
    }
    var rel = ev.key === 'ArrowLeft' ? 'prev' : ev.key === 'ArrowRight' ? 'next' : '';
    if (rel) {
      var link = document.querySelector('.pager a[rel="' + rel + '"]');
      if (link) location.href = link.href;
    }
  });
})();
