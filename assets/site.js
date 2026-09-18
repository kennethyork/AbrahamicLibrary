/* The Abrahamic Library — every script the site has, in one
   file, in the order they depend on each other. Each is a
   self-contained IIFE that does nothing where its elements
   are absent, so one file serves every page. */

/* ===== data.js ===== */
/* The Abrahamic Library — the data layer for the static site.
 *
 * On the PHP site every page asked the server for what it needed. There is no
 * server here beyond a file host, so this file does the same work in the
 * browser: read the catalog, a work's metadata, a chapter out of its packed
 * chunk, the reading plans, the Strong's dictionaries, the citation index.
 *
 * The reading texts are shipped as gzipped chunks of whole chapters
 * (`corpus/<religion>/<work>/c0.json.gz`), one or two megabytes each, built
 * by `tools/pack_corpus.py`. Nothing is guessed: a chapter is fetched, and
 * then decompressed with the browser's own gzip.
 */
(function (global) {
  'use strict';

  /* ---------- small things the templates used everywhere ---------- */

  function e(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  function num(n) {
    var v = Number(n || 0);
    return v.toLocaleString('en-US');
  }

  /* The address of a page, matching inc/boot.php's static_url() exactly:
     one file per kind of page, and the view in the query string. Keep the
     two in step — a link built here that the build did not write is a dead
     link. */
  function u(page, params) {
    params = params || {};
    function qs(pairs) {
      var q = [];
      for (var k in pairs) {
        if (Object.prototype.hasOwnProperty.call(pairs, k) &&
            pairs[k] !== '' && pairs[k] !== null && pairs[k] !== undefined) {
          q.push(encodeURIComponent(k) + '=' + encodeURIComponent(pairs[k]));
        }
      }
      return q.length ? '?' + q.join('&') : '';
    }
    switch (page) {
      case 'index.php': return 'index.html';
      case 'about.php': return 'about.html';
      case 'me.php': return 'me.html';
      case 'plans.php': return 'plans.html';
      case 'plan.php':
        return 'plan.html' + qs({ id: params.id || '' });
      case 'library.php':
        return 'library.html' + qs({
          religion: params.religion, section: params.section,
          p: (parseInt(params.p || 1, 10) || 1) > 1 ? params.p : ''
        });
      case 'work.php':
        return 'work.html' + qs({
          work: params.work,
          p: (parseInt(params.p || 1, 10) || 1) > 1 ? params.p : ''
        });
      default: {
        page = String(page).replace(/\.php$/, '.html');
        var pairs = {};
        for (var k in params) {
          if (Object.prototype.hasOwnProperty.call(params, k)) pairs[k] = params[k];
        }
        return page + qs(pairs);
      }
    }
  }

  function religionName(id) {
    return { judaism: 'Judaism', christianity: 'Christianity', islam: 'Islam' }[id] || id;
  }

  function tierLabel(tier) {
    switch (tier) {
      case 'full': return 'Modernized in full';
      case 'safe': return 'Lightly modernized';
      case 'none': return 'As received';
      default: return 'Modernized';
    }
  }

  function query() {
    var out = {};
    var s = location.search.replace(/^\?/, '');
    if (!s) return out;
    s.split('&').forEach(function (pair) {
      if (!pair) return;
      var i = pair.indexOf('=');
      var k = decodeURIComponent(i === -1 ? pair : pair.slice(0, i));
      var v = i === -1 ? '' : decodeURIComponent(pair.slice(i + 1).replace(/\+/g, ' '));
      if (k.slice(-2) === '[]') {
        (out[k.slice(0, -2)] = out[k.slice(0, -2)] || []).push(v);
      } else {
        out[k] = v;
      }
    });
    return out;
  }

  /* ---------- fetching, compressed or not ----------
     The cache holds promises of the decoded value, not the response, so a
     chapter or a dictionary is fetched once and a second reader of it gets
     the same object rather than a body that has already been read. */

  var cache = {};

  function memo(key, produce) {
    if (!cache[key]) {
      cache[key] = produce();
    }
    return cache[key];
  }

  /* ---------- the bundles ----------
     The reference data and the corpus are each a few large files with an
     index of (offset, length) per part. A host that supports Range answers
     with exactly those bytes and a 206, so asking for one chapter transfers
     one chapter. Where Range is not answered the whole bundle is fetched
     once and the part is cut out of it — correct, only larger.

     Every part is a whole gzip member, so it decompresses on its own,
     without the members around it. */

  var DATA_INDEX = 'data/bundle.json.gz';
  var DATA_BUNDLE = 'data/bundle-%d.bin';

  function bundleIndex() {
    return memo('bi', function () {
      return bodyText(DATA_INDEX).then(function (t) { return JSON.parse(t); });
    });
  }

  /* The bytes of one part, decompressed. A part names the bundle that holds
     it — there may be more than one — its offset, and its length. */
  function partOf(name) {
    return memo('p:' + name, function () {
      return bundleIndex().then(function (index) {
        var entry = index[name];
        if (!entry) throw new Error('no part ' + name);
        var url = DATA_BUNDLE.replace('%d', entry[0]);
        var offset = entry[1], length = entry[2];
        return rangeBytes(url, offset, length);
      });
    });
  }

  /* One gzip member as bytes. */
  function gunzipMember(bytes) {
    if (typeof DecompressionStream !== 'function') {
      return Promise.reject(new Error(
        'This browser cannot read the compressed library; please update it.'));
    }
    return new Response(
      new Response(bytes).body.pipeThrough(new DecompressionStream('gzip'))
    ).arrayBuffer();
  }

  function partText(name) {
    return partOf(name).then(function (buf) {
      return new TextDecoder('utf-8').decode(buf);
    });
  }

  function bundleJson(name) {
    return partText(name).then(function (t) { return JSON.parse(t); });
  }

  /* The response body, as text. A host may send Content-Encoding: gzip for a
     .gz file, in which case the browser has already decompressed it and the
     body is the JSON; otherwise it is decompressed here. */
  function bodyText(url) {
    return memo('t:' + url, function () {
      return fetch(url).then(function (r) {
        if (!r.ok) throw new Error(r.status + ' ' + url);
        if (url.slice(-3) !== '.gz') return r.text();
        var enc = (r.headers.get('content-encoding') || '').toLowerCase();
        if (enc.indexOf('gzip') !== -1) return r.text();
        if (typeof DecompressionStream === 'function' && r.body) {
          return new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).text();
        }
        return Promise.reject(new Error(
          'This browser cannot read the gzipped corpus; please update it.'));
      });
    });
  }

  function fetchText(url) {
    return bodyText(url);
  }

  function fetchJson(url) {
    return memo('j:' + url, function () {
      return bodyText(url).then(function (t) { return JSON.parse(t); });
    });
  }

  /* ---------- the catalog and the works ---------- */

  var DATA = 'data/';
  var CORPUS_URL = 'corpus/';
  var CORPUS_INDEX = CORPUS_URL + 'index.json';
  var CORPUS_META = CORPUS_URL + 'meta.bin';

  var state = {
    catalog: null,
    workIndex: null,
    works: {},
    plans: null,
    strongs: null,
    wordstudy: null,
    wordindex: null,
    daily: null,
    kjvBooks: null,
    canon: {},
    chapters: {}
  };

  function loadCatalog() {
    if (!state.catalog) {
      state.catalog = bundleJson('catalog');
    }
    return state.catalog;
  }

  function catalog() {
    return loadCatalog();
  }

  function religion(id) {
    return loadCatalog().then(function (cat) {
      var hit = null;
      (cat.religions || []).forEach(function (r) { if (r.id === id) hit = r; });
      return hit;
    });
  }

  function buildWorkIndex(cat) {
    if (state.workIndex) return state.workIndex;
    state.workIndex = {};
    (cat.religions || []).forEach(function (r) {
      (r.sections || []).forEach(function (s) {
        (s.works || []).forEach(function (w) {
          state.workIndex[w.id] = { religion: r.id, section: s.id, section_name: s.name, meta: w };
        });
      });
    });
    return state.workIndex;
  }

  /* A work's metadata lives in the corpus metadata bundle: the corpus index
     gives its offset and length, and the whole thing is one range request. */
  function corpusIndex() {
    return memo('cx', function () {
      return bodyText(CORPUS_INDEX).then(function (t) { return JSON.parse(t).works; });
    });
  }

  function work(id) {
    if (state.works[id]) return state.works[id];
    var p = corpusIndex().then(function (index) {
      var entry = index[id];
      if (!entry) return null;
      var religion = entry[0], offset = entry[1], length = entry[2];
      return rangeBytes(CORPUS_META, offset, length).then(function (buf) {
        return JSON.parse(new TextDecoder('utf-8').decode(buf));
      });
    }).catch(function () { return null; });
    state.works[id] = p;
    return p;
  }

  function workTitle(id) {
    return loadCatalog().then(function (cat) {
      var hit = buildWorkIndex(cat)[id];
      return hit ? hit.meta.title : id;
    });
  }

  /* ---------- one chapter, out of its bundle ----------
     Each chapter is its own gzip member in a religion's bundle, and its
     place in that bundle is recorded beside it in the work's metadata:
     [chapter number, title, verse count, bundle number, offset, length]. */

  function chapter(workId, n) {
    var key = workId + '|' + n;
    if (state.chapters[key]) return state.chapters[key];
    var p = work(workId).then(function (meta) {
      if (!meta) return null;
      var entry = null;
      (meta.chapters || []).forEach(function (c) {
        if (String(c[0]) === String(n)) entry = c;
      });
      if (!entry) return null;
      /* The chapter's place in its bundle is known from the metadata, so
         this is one range request and no index lookup. */
      var bundle = entry[3], offset = entry[4], length = entry[5];
      var url = CORPUS_URL + meta.religion + '/b' + bundle + '.bin';
      return rangeBytes(url, offset, length).then(function (buf) {
        return JSON.parse(new TextDecoder('utf-8').decode(buf));
      });
    });
    state.chapters[key] = p;
    return p;
  }

  /* The bytes of a range, decompressed if they are a gzip member. */
  function rangeBytes(url, offset, length) {
    return memo('r:' + url + '#' + offset + '+' + length, function () {
      return fetch(url, {
        headers: { Range: 'bytes=' + offset + '-' + (offset + length - 1) }
      }).then(function (r) {
        if (r.status === 206) return r.arrayBuffer();
        if (!r.ok) throw new Error(r.status + ' ' + url);
        /* No range support: the whole bundle came back; take the part. */
        return r.arrayBuffer().then(function (buf) {
          return buf.slice(offset, offset + length);
        });
      }).then(gunzipMember);
    });
  }

  function neighbours(meta, n) {
    var list = (meta.chapters || []).map(function (c) { return c[0]; });
    var i = list.indexOf(String(n));
    return [i > 0 ? list[i - 1] : null,
            i !== -1 && i + 1 < list.length ? list[i + 1] : null];
  }

  /* ---------- the canonical books and the composite Bibles ---------- */

  var CANON_FILES = {
    'kjv-bible': 'kjv_canon.json',
    'webu-bible': 'webu-bible_canon.json',
    'dr-bible': 'dr-bible_canon.json'
  };

  function canonMap(workId) {
    var file = CANON_FILES[workId];
    if (!file) return Promise.resolve({});
    if (!state.canon[file]) state.canon[file] = bundleJson(file.replace('.json', ''));
    return state.canon[file];
  }

  function canonBook(workId) {
    return bundleJson('links/books').then(function (books) {
      var b = books[workId];
      return b ? { key: b[0], label: b[1] } : null;
    });
  }

  function canonRef(workId, chapterN) {
    return canonMap(workId).then(function (map) {
      if (Object.keys(map).length) {
        var hit = map[chapterN];
        return hit ? [hit[0], String(hit[1])] : null;
      }
      return canonBook(workId).then(function (book) {
        return book ? [book.key, String(chapterN)] : null;
      });
    });
  }

  function canonGlobal(workId, bookKey, localChapter) {
    return canonMap(workId).then(function (map) {
      for (var g in map) {
        if (map[g] && map[g][0] === bookKey && String(map[g][1]) === String(localChapter)) {
          return String(g);
        }
      }
      return null;
    });
  }

  /* ---------- the citation index ---------- */

  function linksRead(rel) {
    return bundleJson('links/' + rel.replace(/\.json$/, ''));
  }

  function citationCounts(bookKey, chapterN) {
    if (!/^[a-z0-9-]+$/.test(bookKey) || !/^\d+$/.test(String(chapterN))) {
      return Promise.resolve({});
    }
    return linksRead(bookKey + '/totals').then(function (t) {
      var out = {};
      var row = t && t[chapterN] ? t[chapterN] : {};
      for (var v in row) out[String(v)] = Number(row[v]);
      return out;
    }).catch(function () { return {}; });
  }

  function citedBy(target, limit) {
    var bits = String(target).split('|');
    if (bits.length !== 3) return Promise.resolve([]);
    return linksRead(bits[0] + '/' + bits[1]).then(function (rows) {
      var list = (rows && rows[bits[2]]) || [];
      return list.slice(0, limit || 300);
    }).catch(function () { return []; });
  }

  function linkBooks() {
    return bundleJson('links/books').catch(function () { return {}; });
  }

  /* ---------- plans, Strong's, word study, the daily verse ---------- */

  function plans() {
    if (!state.plans) state.plans = bundleJson('plans');
    return state.plans.then(function (d) { return (d && d.plans) || []; });
  }

  function plan(id) {
    return plans().then(function (all) {
      var hit = null;
      all.forEach(function (p) { if (p.id === id) hit = p; });
      return hit;
    });
  }

  function strongs() {
    if (!state.strongs) {
      state.strongs = bundleJson('strongs').then(function (d) {
        return d && d.entries ? d : { entries: {}, english: {} };
      });
    }
    return state.strongs;
  }

  function strongsEntry(id) {
    return strongs().then(function (s) { return s.entries[id] || null; });
  }

  function strongsByEnglish(word) {
    return strongs().then(function (s) {
      var out = [];
      ((s.english || {})[word] || []).forEach(function (hit) {
        var entry = s.entries[hit.id];
        if (entry) {
          out.push(Object.assign({}, entry, { id: hit.id, rank: hit.rank || null }));
        }
      });
      out.sort(function (a, b) {
        if (a.lang !== b.lang) return a.lang < b.lang ? -1 : 1;
        return Number(a.num) - Number(b.num);
      });
      return out;
    });
  }

  var COMMON = {
    shalom: 'shalowm', 'shalôm': 'shalowm', shalowm: 'shalowm',
    elohim: 'elohiym', elohiym: 'elohiym',
    hallelujah: 'halal', hallelu: 'halal', halal: 'halal',
    amen: 'amen', torah: 'towrah', kadosh: 'qadowsh', moshiach: 'mashiyach'
  };

  function ascii(w) {
    w = String(w).toLowerCase();
    return w.replace(/[\u00c0-\u024f]/g, function (ch) {
      return ch.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }).replace(/^['"`\u2019]+/, '');
  }

  function strongsByWord(word) {
    return strongs().then(function (s) {
      var target = ascii(word);
      target = COMMON[target] || target;
      if (!target) return [];
      var out = [];
      for (var id in s.entries) {
        var w = ascii(s.entries[id].word || '');
        if (w === target || w.indexOf(target) === 0) {
          out.push(Object.assign({}, s.entries[id], { id: id }));
        }
      }
      out.sort(function (a, b) { return Number(a.num) - Number(b.num); });
      return out.slice(0, 40);
    });
  }

  function wordstudy() {
    if (!state.wordstudy) {
      state.wordstudy = bundleJson('wordstudy').then(function (d) {
        return d || { families: [], samples: [], intro: '' };
      });
    }
    return state.wordstudy;
  }

  function wordindex() {
    if (!state.wordindex) state.wordindex = bundleJson('wordindex');
    return state.wordindex;
  }

  function daily() {
    if (!state.daily) state.daily = bundleJson('daily');
    return state.daily;
  }

  function verseOfTheDay() {
    return daily().then(function (d) {
      var all = (d && d.verses) || [];
      if (!all.length) return null;
      var day = Math.floor(Date.now() / 86400000);
      return all[day % all.length];
    });
  }

  /* ---------- editions of the same book ---------- */

  function editionsOf(meta) {
    return loadCatalog().then(function (cat) {
      var out = [];
      var whole = (meta.section || '') === 'whole-bible';
      (cat.religions || []).forEach(function (r) {
        (r.sections || []).forEach(function (s) {
          (s.works || []).forEach(function (w) {
            if (w.id === meta.id || w.borrowed_from) return;
            if (whole) {
              if (s.id === 'whole-bible') out.push(w);
              return;
            }
            if (String(w.title).toLowerCase() === String(meta.title).toLowerCase()) {
              out.push(w);
            }
          });
        });
      });
      return out;
    });
  }

  /* ---------- alignment, for the word study ---------- */

  function align(bookKey, chapterN) {
    return bundleJson('align/' + bookKey + '/' + chapterN)
      .catch(function () { return null; });
  }

  /* ---------- the KJV reference index (autocomplete, references) ---------- */

  function kjvBooks() {
    if (!state.kjvBooks) state.kjvBooks = bundleJson('kjv_books');
    return state.kjvBooks;
  }

  global.AA = {
    e: e, num: num, u: u, query: query,
    religionName: religionName, tierLabel: tierLabel,
    fetchJson: fetchJson, fetchText: fetchText, part: partText,
    catalog: catalog, religion: religion, work: work, workTitle: workTitle,
    chapter: chapter, neighbours: neighbours,
    canonBook: canonBook, canonRef: canonRef, canonGlobal: canonGlobal,
    citationCounts: citationCounts, citedBy: citedBy, linkBooks: linkBooks,
    plans: plans, plan: plan,
    strongs: strongs, strongsEntry: strongsEntry,
    strongsByEnglish: strongsByEnglish, strongsByWord: strongsByWord,
    wordstudy: wordstudy, wordindex: wordindex, daily: daily,
    verseOfTheDay: verseOfTheDay, editionsOf: editionsOf, align: align,
    kjvBooks: kjvBooks
  };
})(window);

/* ===== porter.js ===== */
/* The Porter stemming algorithm, 1980 — the browser's copy.
 *
 * This is the same algorithm as tools/porter.py, which built the search
 * index, so a query stems exactly as the text was stemmed. It is a port of
 * Martin Porter's own ANSI C implementation, including the departures the
 * paper does not mention (two-letter words are left alone, -bli becomes
 * -ble, -logi becomes -log).
 */
(function (global) {
  'use strict';

  function Stemmer(p) {
    this.b = p.split('');
    this.k0 = 0;
    this.k = p.length - 1;
    this.j = 0;
  }

  Stemmer.prototype.cons = function (i) {
    var ch = this.b[i];
    if (ch === 'a' || ch === 'e' || ch === 'i' || ch === 'o' || ch === 'u') return false;
    if (ch === 'y') return i === this.k0 ? true : !this.cons(i - 1);
    return true;
  };

  Stemmer.prototype.m = function () {
    var n = 0;
    var i = this.k0;
    for (;;) {
      if (i > this.j) return n;
      if (!this.cons(i)) break;
      i++;
    }
    i++;
    for (;;) {
      for (;;) {
        if (i > this.j) return n;
        if (this.cons(i)) break;
        i++;
      }
      i++;
      n++;
      for (;;) {
        if (i > this.j) return n;
        if (!this.cons(i)) break;
        i++;
      }
      i++;
    }
  };

  Stemmer.prototype.vowelinstem = function () {
    for (var i = this.k0; i <= this.j; i++) if (!this.cons(i)) return true;
    return false;
  };

  Stemmer.prototype.doublec = function (j) {
    if (j < this.k0 + 1) return false;
    if (this.b[j] !== this.b[j - 1]) return false;
    return this.cons(j);
  };

  Stemmer.prototype.cvc = function (i) {
    if (i < this.k0 + 2 || !this.cons(i) || this.cons(i - 1) || !this.cons(i - 2)) return false;
    var ch = this.b[i];
    return ch !== 'w' && ch !== 'x' && ch !== 'y';
  };

  Stemmer.prototype.ends = function (s) {
    var length = s.length;
    if (this.b[this.k] !== s.charAt(length - 1)) return false;
    if (length > this.k - this.k0 + 1) return false;
    for (var i = 0; i < length; i++) {
      if (this.b[this.k - length + 1 + i] !== s.charAt(i)) return false;
    }
    this.j = this.k - length;
    return true;
  };

  Stemmer.prototype.setto = function (s) {
    this.b.splice(this.j + 1, this.k - this.j, null);
    for (var i = 0; i < s.length; i++) this.b[this.j + 1 + i] = s.charAt(i);
    this.k = this.j + s.length;
  };

  Stemmer.prototype.r = function (s) {
    if (this.m() > 0) this.setto(s);
  };

  Stemmer.prototype.step1ab = function () {
    if (this.b[this.k] === 's') {
      if (this.ends('sses')) this.k -= 2;
      else if (this.ends('ies')) this.setto('i');
      else if (this.b[this.k - 1] !== 's') this.k--;
    }
    if (this.ends('eed')) {
      if (this.m() > 0) this.k--;
    } else if ((this.ends('ed') || this.ends('ing')) && this.vowelinstem()) {
      this.k = this.j;
      if (this.ends('at')) this.setto('ate');
      else if (this.ends('bl')) this.setto('ble');
      else if (this.ends('iz')) this.setto('ize');
      else if (this.doublec(this.k)) {
        this.k--;
        if (this.b[this.k] === 'l' || this.b[this.k] === 's' || this.b[this.k] === 'z') this.k++;
      } else if (this.m() === 1 && this.cvc(this.k)) this.setto('e');
    }
  };

  Stemmer.prototype.step1c = function () {
    if (this.ends('y') && this.vowelinstem()) this.b[this.k] = 'i';
  };

  Stemmer.prototype.step2 = function () {
    var ch = this.b[this.k - 1];
    if (ch === 'a') {
      if (this.ends('ational')) this.r('ate');
      else if (this.ends('tional')) this.r('tion');
    } else if (ch === 'c') {
      if (this.ends('enci')) this.r('ence');
      else if (this.ends('anci')) this.r('ance');
    } else if (ch === 'e') {
      if (this.ends('izer')) this.r('ize');
    } else if (ch === 'l') {
      if (this.ends('bli')) this.r('ble');
      else if (this.ends('alli')) this.r('al');
      else if (this.ends('entli')) this.r('ent');
      else if (this.ends('eli')) this.r('e');
      else if (this.ends('ousli')) this.r('ous');
    } else if (ch === 'o') {
      if (this.ends('ization')) this.r('ize');
      else if (this.ends('ation')) this.r('ate');
      else if (this.ends('ator')) this.r('ate');
    } else if (ch === 's') {
      if (this.ends('alism')) this.r('al');
      else if (this.ends('iveness')) this.r('ive');
      else if (this.ends('fulness')) this.r('ful');
      else if (this.ends('ousness')) this.r('ous');
    } else if (ch === 't') {
      if (this.ends('aliti')) this.r('al');
      else if (this.ends('iviti')) this.r('ive');
      else if (this.ends('biliti')) this.r('ble');
    } else if (ch === 'g') {
      if (this.ends('logi')) this.r('log');
    }
  };

  Stemmer.prototype.step3 = function () {
    var ch = this.b[this.k];
    if (ch === 'e') {
      if (this.ends('icate')) this.r('ic');
      else if (this.ends('ative')) this.r('');
      else if (this.ends('alize')) this.r('al');
    } else if (ch === 'i') {
      if (this.ends('iciti')) this.r('ic');
    } else if (ch === 'l') {
      if (this.ends('ical')) this.r('ic');
      else if (this.ends('ful')) this.r('');
    } else if (ch === 's') {
      if (this.ends('ness')) this.r('');
    }
  };

  Stemmer.prototype.step4 = function () {
    var ch = this.b[this.k - 1];
    var ok = false;
    if (ch === 'a') ok = this.ends('al');
    else if (ch === 'c') ok = this.ends('ance') || this.ends('ence');
    else if (ch === 'e') ok = this.ends('er');
    else if (ch === 'i') ok = this.ends('ic');
    else if (ch === 'l') ok = this.ends('able') || this.ends('ible');
    else if (ch === 'n') ok = this.ends('ant') || this.ends('ement') || this.ends('ment') || this.ends('ent');
    else if (ch === 'o') {
      if (this.ends('ion') && this.j >= this.k0 && (this.b[this.j] === 's' || this.b[this.j] === 't')) ok = true;
      else ok = this.ends('ou');
    } else if (ch === 's') ok = this.ends('ism');
    else if (ch === 't') ok = this.ends('ate') || this.ends('iti');
    else if (ch === 'u') ok = this.ends('ous');
    else if (ch === 'v') ok = this.ends('ive');
    else if (ch === 'z') ok = this.ends('ize');
    if (ok && this.m() > 1) this.k = this.j;
  };

  Stemmer.prototype.step5 = function () {
    this.j = this.k;
    if (this.b[this.k] === 'e') {
      var a = this.m();
      if (a > 1 || (a === 1 && !this.cvc(this.k - 1))) this.k--;
    }
    if (this.b[this.k] === 'l' && this.doublec(this.k) && this.m() > 1) this.k--;
  };

  function porter(p) {
    if (p.length <= 2) return p;
    var s = new Stemmer(p);
    s.step1ab();
    if (s.k > s.k0) {
      s.step1c();
      s.step2();
      s.step3();
      s.step4();
      s.step5();
    }
    return s.b.slice(0, s.k + 1).join('');
  }

  global.AAPorter = porter;
})(typeof window !== 'undefined' ? window : globalThis);

/* ===== app.js ===== */
/* The Abrahamic Library — vanilla JS, no libraries.
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
    var here = { url: location.pathname.split('/').pop() + location.search };

    function isMarked() {
      return bookmarks().some(function (b) { return b.url === here.url; });
    }

    function paint() {
      var on = isMarked();
      markBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
      markBtn.textContent = on ? 'Bookmarked' : 'Bookmark';
    }

    markBtn.addEventListener('click', function () {
      /* The label is the work and chapter, which the static reader sets on
         the button once its data has arrived, so it is read here rather
         than at load time. */
      here.label = markBtn.dataset.bookmark || document.title;
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

/* ===== study.js ===== */
/* The Abrahamic Library — the study layer.
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
      url:   (window.AA ? AA.u('read.php', { work: reader.dataset.work, c: reader.dataset.c })
                       : 'read.php?work=' + encodeURIComponent(reader.dataset.work)
                         + '&c=' + encodeURIComponent(reader.dataset.c)),
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

  /* Everything that reads the chapter waits for it to be on the page. On the
     PHP site it always is; on a static host assets/read.js draws it after its
     data arrives and sets data-painted, so this runs then instead. The
     history entry is written either way, because where you were does not
     need the text. */
  function init() {
  if (!reader || reader.dataset.verses !== '1') { remember(); paintLists(); return; }
  remember();

  /* ---------- the text as it was printed ----------
     The archive's whole claim is that it changed how a text says a thing and
     not what it says. That is only checkable if the words that were there are
     still there, so the ingesters keep both and this puts the old one back on
     the page. Only verses that actually changed carry a `data-src`; the rest
     were already modern and have nothing to show. */
  var printed = false;
  var asPrinted = document.querySelector('[data-as-printed]');
  var changed = document.querySelectorAll('.scripture [data-src]');

  if (asPrinted && changed.length) {
    asPrinted.hidden = false;
    asPrinted.title = changed.length + ' of these were modernized';
    asPrinted.addEventListener('click', function () {
      printed = !printed;
      changed.forEach(function (el) {
        var slot = el.querySelector('.t');
        if (!slot) return;
        if (printed) {
          if (!el.dataset.mod) el.dataset.mod = slot.textContent;
          slot.textContent = el.dataset.src;
        } else if (el.dataset.mod) {
          slot.textContent = el.dataset.mod;
        }
      });
      asPrinted.setAttribute('aria-pressed', printed ? 'true' : 'false');
      asPrinted.textContent = printed ? 'Modernized' : 'As printed';
      document.querySelector('.scripture').classList.toggle('as-printed', printed);
      relayout();
    });
  }

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
    box.querySelectorAll('.mnote.mine').forEach(function (n) { n.remove(); });

    /* The reader's own notes come first. */
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

    /* Then the words as printed, on every changed verse the reader has not
       written on: their pencil takes the place. */
    var wrote = {};
    here.forEach(function (n) {
      wrote[String(n.v).charAt(0) === 'p'
        ? n.v : 'v' + String(n.v).replace(/[^0-9a-z]/gi, '')] = true;
    });
    var printed = 0;
    changed.forEach(function (el) {
      var src = el.dataset.src;
      if (!src || wrote[el.id]) return;
      var p = document.createElement('div');
      p.className = 'mnote printed';
      p.dataset.for = el.id;
      var b = document.createElement('b');
      b.textContent = (el.dataset.ref || '').split(':').pop();
      var t = document.createElement('span');
      t.className = 'mnote-text';
      t.textContent = src;
      p.appendChild(b); p.appendChild(t);
      box.appendChild(p);
      printed++;
    });

    var title = box.querySelector('[data-margin-title]');
    if (title) {
      title.textContent = here.length ? 'Your notes' : 'As printed';
    }
    box.hidden = here.length === 0 && printed === 0;
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
      var slot = el.querySelector('.t');
      var body = slot ? slot.textContent.trim()
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
    if (ev.key === 'Escape') { if (chosen.length) clearChoice(); }
  });

  paintVerses();
  }   /* init() */

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

  if (!reader || reader.dataset.verses !== '1') {
    remember();
    paintLists();
  } else if (reader.dataset.static === '1' && reader.dataset.painted !== '1') {
    document.addEventListener('aa:chapter', function () { init(); }, { once: true });
  } else {
    init();
  }
})();

/* ===== wordstudy.js ===== */
/* The Abrahamic Library — the in-reader word study.
   Selecting a verse and pressing "Words" shows the Hebrew or Greek standing
   behind that verse.

   For a canonical work — one that data/align knows — it shows the original
   text itself, word by word, in order, each with its Strong number and the
   plain-English note this archive gives it. That is the true interlinear,
   aligned to the verse from the original-language source rather than guessed
   from an English rendering: for Gen 1:3 it shows אור / H216, not a list of
   every word English ever called "light".

   For everything else (commentary, Talmud, Qur'an) it falls back to the
   candidate panel: the Hebrew/Greek words that the King James translators
   rendered by the same English word, ranked by how often they used it.

   Both draw on a compact local index and stay on this device; nothing is
   sent anywhere. The alignment files are tiny per chapter and fetched only
   when someone asks. */
(function () {
  'use strict';

  var reader = document.querySelector('[data-reader]');
  var panel = document.querySelector('[data-words-panel]');
  var bodyEl = document.querySelector('[data-words-body]');
  var subjectEl = document.querySelector('[data-words-subject]');
  var candidateIndex = null;      /* data/wordindex.json, for the fallback */
  var align = null;               /* data/align/<book>/<chapter>.json */

  if (!reader || !panel || !('fetch' in window)) return;

  var canonical = (reader.dataset.canon || '').trim();
  var chapterNo = (reader.dataset.canonCh || reader.dataset.c || '').trim();

  /* The chosen verses live in study.js's DOM selection, reached the same way
     study.js reads them: `.scripture .v.sel` / `.pb.sel`. */
  function chosenVerses() {
    return Array.prototype.slice.call(
      document.querySelectorAll('.scripture .v.sel, .scripture .pb.sel'));
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-act="words"]');
    if (b) { ev.preventDefault(); render(); }
  });

  function render() {
    var chosen = chosenVerses();
    var subject = chosen.length === 1
      ? (chosen[0].dataset.ref || 'This verse')
      : (chosen.length + ' verses selected');
    subjectEl.textContent = subject;
    bodyEl.textContent = '';

    if (!chosen.length) { close(); return; }

    /* Canonical work with alignment: show the original language, word by
       word. Otherwise (non-canonical, or chapter missing) fall back. */
    if (canonical) {
      var key = canonical + '/' + chapterNo;
      if (align !== null && align.__f === key) { fillAlign(chosen, align); return; }
      bodyEl.textContent = 'Reading the original…';
      panel.hidden = false;
      /* AA.align answers with the data itself; the plain fetch with a
         response, for the hosted app where there is no data layer. */
      var source = window.AA
        ? AA.align(canonical, chapterNo)
        : fetch('data/align/' + encodeURIComponent(key) + '.json')
            .then(function (r) { return r.ok ? r.json() : null; });
      source.then(function (d) {
        if (!d) { fallback(chosen); return; }
        align = d; align.__f = key;
        fillAlign(chosen, d);
      }).catch(function () { fallback(chosen); });
      return;
    }
    fallback(chosen);
  }

  /* ---------- interlinear (canonical) ---------- */
  function loadCandidates(done) {
    if (candidateIndex) { done(candidateIndex); return; }
    var source = window.AA
      ? AA.wordindex()
      : fetch('data/wordindex.json').then(function (r) { return r.json(); });
    source.then(function (d) { candidateIndex = d; done(d); })
      .catch(function () { done(null); });
  }

  function fillAlign(chosen, data) {
    loadCandidates(function (idx) {
      var frag = document.createDocumentFragment();
      var showed = 0;
      // Verses with no original text in the index (Mark 16:9-20, the woman
      // taken in adultery, etc.) fall back to the candidate panel rather
      // than silently vanishing.
      var fallbackThese = [];

      chosen.forEach(function (el) {
        var v = String(el.dataset.v || '').replace(/^p+/, '');
        var words = (data[v] || []).filter(function (p) { return p && p.length; });
        if (!words.length) { fallbackThese.push(el); return; }

        var card = makeEl('div', '', 'wx');
        var head = makeEl('div', '', 'wx-head');
        head.appendChild(makeEl('b', (el.dataset.ref || ('Verse ' + v)) +
          ' — in the original'));
        card.appendChild(head);

        words.forEach(function (pair) {
          var strongId = pair[0], original = pair[1];
          var meta = (idx && idx.entries[strongId]) || [];
          var lang = meta[0] === 'hebrew' ? 'Hebrew' : 'Greek';
          var art = makeEl('div', '');
          art.className = 'wx-art wx-inter';
          art.setAttribute('data-r',
            meta[0] === 'hebrew' ? 'judaism' : 'christianity');
          var orig = makeEl('b', original, 'wx-original');
          art.appendChild(orig);
          var idlink = makeEl('a', strongId, 'wx-id');
          idlink.href = (window.AA ? AA.u('strongs.php', { q: strongId })
                                   : 'strongs.php?q=' + encodeURIComponent(strongId));
          idlink.title = lang + (meta[1] ? ' · ' + meta[1] : '');
          var gloss = (idx && idx.plain[strongId]) || '';
          art.appendChild(idlink);
          if (meta[1]) art.setAttribute('title', meta[1]);
          if (gloss) art.appendChild(makeEl('span', gloss, 'wx-plain'));
          card.appendChild(art);
          showed++;
        });
        frag.appendChild(card);
      });

      bodyEl.textContent = '';
      if (!showed && !fallbackThese.length) {
        panel.hidden = false;
        bodyEl.textContent = 'The original of this passage is not in the index.';
        return;
      }
      // render the interlinear cards
      if (frag.childNodes.length) bodyEl.appendChild(frag);
      // render candidate cards for the verses with no original
      if (fallbackThese.length) {
        buildFallbackCards(fallbackThese, idx, bodyEl);
      }
      panel.hidden = false;
    });
  }

  /* ---------- fallback (non-canonical / candidate panel) ---------- */
  function fallback(chosen) {
    loadCandidates(function (idx) {
      if (!idx) { bodyEl.textContent = 'Could not load the word index.'; return; }
      bodyEl.textContent = '';
      buildFallbackCards(chosen, idx, bodyEl);
      panel.hidden = false;
    });
  }

  /* Render candidate cards for a set of chosen verses into a parent element.
     Shared by the pure fallback and by canonical chapters that have no
     original text for some verses. */
  function buildFallbackCards(chosen, idx, parent) {
    var body = chosen.map(function (el) {
      var slot = el.querySelector('.t');
      return slot ? slot.textContent.trim()
        : el.textContent.replace(/^\s*\S+\s*/, '').trim();
    }).join(' ');

    var words = lookupWords(body, idx);
    var frag = document.createDocumentFragment();
    words.forEach(function (w) {
      var rows = wordRows(idx, w.stem);
      var card = makeEl('div', '', 'wx');
      var head = makeEl('div', '', 'wx-head');
      head.appendChild(makeEl('b', cap(w.term)));
      card.appendChild(head);
      rows.forEach(function (r) {
        var art = makeEl('div', '', 'wx-art');
        art.setAttribute('data-r', r.religion);
        var row = makeEl('div', '', 'wx-art-head');
        var link = makeEl('a', r.id, 'wx-id');
        link.href = (window.AA ? AA.u('strongs.php', { q: r.id })
                               : 'strongs.php?q=' + encodeURIComponent(r.id));
        row.appendChild(link);
        row.appendChild(makeEl('span', r.word, 'wx-word'));
        row.appendChild(makeEl('span', r.lang, ' '));
        art.appendChild(row);
        if (r.plain) art.appendChild(makeEl('p', r.plain, 'wx-plain'));
        if (r.rank) art.appendChild(makeEl('p',
          'Used ' + r.rank + '× by the King James', 'wx-rank small muted'));
        card.appendChild(art);
      });
      frag.appendChild(card);
    });
    if (!frag.childNodes.length) {
      parent.appendChild(makeEl('p', 'No ordinary words here to look up.',
        'wx-empty muted small'));
    } else {
      parent.appendChild(frag);
    }
  }

  function wordRows(idx, stem) {
    var rows = (idx.words[stem] || []).map(function (hit) {
      var meta = idx.entries[hit[0]] || [];
      return {
        id: hit[0], word: meta[1] || hit[0],
        lang: meta[0] === 'hebrew' ? 'Hebrew' : 'Greek',
        rank: hit[1] || 0,
        religion: meta[0] === 'hebrew' ? 'judaism' : 'christianity',
        plain: idx.plain[hit[0]] || ''
      };
    }).sort(function (a, b) { return (a.rank || 0) - (b.rank || 0); });
    return rows;
  }

  function lookupWords(text, idx) {
    var seen = Object.create(null), out = [];
    var raw = String(text || '').match(/[A-Za-z']+/g) || [];
    raw.forEach(function (w) {
      var s = strip(w), t = stem(s, idx);
      if (!s || !idx.words[t] || seen[s]) return;
      seen[s] = true;
      if (out.indexOf(w) === -1) out.push({ term: s, stem: t });
    });
    out.sort(function (a, b) { return b.stem.length - a.stem.length; });
    return out.slice(0, 8);
  }

  function stem(s, idx) {
    if (idx.words[s]) return s;
    var t = s;
    if (t.length > 3 && t.slice(-2) === 'ed' && idx.words[t.slice(0, -1)]) {
      t = t.slice(0, -1);
    }
    if (!idx.words[t] && t.length > 4 && t.slice(-1) === 's') t = t.slice(0, -1);
    if (!idx.words[t] && t.length > 5 && t.slice(-3) === 'ing') t = t.slice(0, -3);
    return t;
  }

  function strip(s) {
    return String(s || '').trim().replace(/[’'"‘]/g, '').toLowerCase();
  }

  function close() {
    panel.hidden = true;
    if (bodyEl) bodyEl.textContent = '';
  }

  function closeOnOther(ev) {
    if (ev.target.closest('[data-act="words"]')) return;
    if (ev.target.closest('[data-words-panel]')) return;
    if (ev.target.closest('[data-act="note"]')) { close(); return; }
    if (!ev.target.closest('[data-vbar]')) close();
  }
  document.addEventListener('click', closeOnOther);

  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
  function makeEl(tag, text, cls) {
    var el = document.createElement(tag);
    if (text !== undefined && text !== '') el.textContent = text;
    if (cls) el.className = cls;
    return el;
  }
})();

/* ===== search.js ===== */
/* Autocomplete for the header search box: suggest book names and references
   as the reader types. Reads the KJV book list from a tiny endpoint. */
(function () {
  'use strict';

  var input = document.getElementById('q');
  if (!input || input.dataset.ac === 'off') return;

  var box = document.createElement('div');
  box.className = 'ac';
  box.hidden = true;
  input.parentNode.appendChild(box);

  var books = null;
  var timer = null;

  function loadBooks(cb) {
    if (books) { cb(books); return; }
    (window.AA
      ? AA.part('kjv_books')
          .then(function (t) { return JSON.parse(t); })
      : fetch('data/kjv_books.json').then(function (r) { return r.json(); }))
      .then(function (d) {
        /* The list's own addresses are the application's (`read.php?…`);
           on a file host the reading page is a file, so ask AA for it. */
        books = d.map(function (b) {
          if (!window.AA) return b;
          var m = /work=([^&]+)&c=([^&]+)/.exec(b.url || '');
          return m ? { label: b.label, url: AA.u('read.php', { work: m[1], c: m[2] }) } : b;
        });
        cb(books);
      })
      .catch(function () { cb([]); });
  }

  function show(list) {
    box.innerHTML = '';
    if (!list.length) { box.hidden = true; return; }
    list.forEach(function (item) {
      var a = document.createElement('a');
      a.href = item.url;
      a.textContent = item.label;
      a.addEventListener('mousedown', function (e) { e.preventDefault(); });
      box.appendChild(a);
    });
    box.hidden = false;
  }

  input.addEventListener('input', function () {
    clearTimeout(timer);
    var v = input.value.trim();
    if (v.length < 2) { box.hidden = true; return; }
    timer = setTimeout(function () {
      loadBooks(function (all) {
        var low = v.toLowerCase();
        var hits = all.filter(function (b) {
          return b.label.toLowerCase().indexOf(low) !== -1;
        }).slice(0, 8);
        show(hits);
      });
    }, 120);
  });

  document.addEventListener('click', function (e) {
    if (!box.contains(e.target)) box.hidden = true;
  });
})();

/* ===== plan.js ===== */
/* Reading-plan progress. A plan is a list of days; what is kept is the set of
   days you have ticked, per plan, in this browser. */
(function () {
  'use strict';

  function read(k, d) {
    try { return JSON.parse(localStorage.getItem('aa.' + k)) || d; }
    catch (e) { return d; }
  }
  function write(k, v) {
    try { localStorage.setItem('aa.' + k, JSON.stringify(v)); } catch (e) { /* full */ }
  }

  var all = read('plans', {});          /* { planId: [dayIndex, …] } */

  function done(id) { return all[id] || []; }

  function paintBar(box, count, total) {
    if (!box) return;
    var pct = total ? Math.round((count / total) * 100) : 0;
    var fill = box.querySelector('.bar > span');
    var text = box.querySelector('em');
    if (fill) fill.style.width = pct + '%';
    if (text) {
      text.textContent = count
        ? count + ' of ' + total + ' days — ' + pct + '%'
        : total + ' days, not started';
    }
    box.hidden = false;
    box.classList.toggle('complete', total > 0 && count === total);
  }

  /* ---------- the list of plans ---------- */
  document.querySelectorAll('[data-plan-card]').forEach(function (card) {
    var id = card.dataset.planCard;
    var total = +card.dataset.days || 0;
    var n = done(id).length;
    if (n) paintBar(card.querySelector('[data-plan-progress]'), n, total);
  });

  /* ---------- one plan ---------- */
  var holder = document.querySelector('[data-plan]');
  if (!holder) return;

  /* On a static host the plan's days are drawn by assets/planpage.js after
     data/plans.json arrives, so the list is read then. On the PHP site the
     days are already in the page and this runs at once. */
  if (!holder.querySelector('.plan-day') &&
      holder.dataset.staticReady !== undefined) {
    document.addEventListener('aa:plan', function () { run(); }, { once: true });
    return;
  }
  run();

  function run() {
  var id    = holder.dataset.plan;
  var days  = Array.prototype.slice.call(holder.querySelectorAll('.plan-day'));
  var box   = document.querySelector('[data-plan-progress]');

  function paint() {
    var set = done(id);
    days.forEach(function (li) {
      var i  = +li.dataset.day;
      var on = set.indexOf(i) !== -1;
      li.classList.toggle('done', on);
      var cb = li.querySelector('input');
      if (cb) cb.checked = on;
    });
    paintBar(box, set.length, days.length);

    /* Today is the first day not yet ticked — which is what a reader means
       by "where I was", rather than the calendar. */
    var next = days.find(function (li) { return !li.classList.contains('done'); })
            || days[days.length - 1];
    var jump = document.querySelector('[data-plan-jump]');
    if (jump && next) {
      jump.setAttribute('href', '#' + next.id);
      jump.textContent = set.length === days.length
        ? 'Finished — read it again'
        : (set.length ? 'Go to day ' + (+next.dataset.day + 1)
                      : 'Start at day 1');
    }
  }

  holder.addEventListener('change', function (ev) {
    var cb = ev.target.closest('[data-plan-done]');
    if (!cb) return;
    var i = +cb.dataset.planDone;
    var set = done(id).filter(function (x) { return x !== i; });
    if (cb.checked) set.push(i);
    set.sort(function (a, b) { return a - b; });
    all[id] = set;
    write('plans', all);
    paint();
  });

  var reset = document.querySelector('[data-plan-reset]');
  if (reset) {
    reset.addEventListener('click', function () {
      delete all[id];
      write('plans', all);
      paint();
    });
  }

  paint();
  }   /* run() */
})();

/* ===== pwa.js ===== */
/* Registering the service worker, offering the install, and letting a reading
   plan be saved for a week away from the network. */
(function () {
  'use strict';

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('sw.js').catch(function () {
        /* Off a secure origin — file:// or plain http on a LAN address —
           registration is refused by the browser, and the site works
           exactly as it did before. Nothing to report. */
      });
    });
  }

  /* ---------- the install prompt ----------
     Chrome hands over the event and expects it back later; Safari never
     fires it, and shows its own Add to Home Screen. So the button appears
     only where there is something for it to do. */
  var deferred = null;
  var btn = document.querySelector('[data-install]');

  window.addEventListener('beforeinstallprompt', function (ev) {
    ev.preventDefault();
    deferred = ev;
    if (btn) btn.hidden = false;
  });

  if (btn) {
    btn.addEventListener('click', function () {
      if (!deferred) return;
      deferred.prompt();
      deferred.userChoice.then(function () { deferred = null; btn.hidden = true; });
    });
  }

  window.addEventListener('appinstalled', function () {
    if (btn) btn.hidden = true;
  });

  /* ---------- saving a plan for offline ---------- */
  var save = document.querySelector('[data-plan-save]');
  if (save && 'serviceWorker' in navigator) {
    save.hidden = false;
    save.addEventListener('click', function () {
      var urls = Array.prototype.map.call(
        document.querySelectorAll('.plan-links a'),
        function (a) { return a.getAttribute('href'); });
      if (!urls.length) return;
      save.disabled = true;
      save.textContent = 'Saving ' + urls.length + ' chapters…';
      navigator.serviceWorker.ready.then(function (reg) {
        var ch = new MessageChannel();
        ch.port1.onmessage = function (ev) {
          var d = ev.data || {};
          save.textContent = 'Saved ' + d.kept + ' of ' + d.of + ' for offline';
          save.disabled = false;
        };
        reg.active.postMessage({ type: 'keep', urls: urls }, [ch.port2]);
      });
    });
  }
})();

/* ===== me.js ===== */
/* Reads back everything the study layer saved, and hands it over on request.
   Nothing here talks to the server. */
(function () {
  'use strict';

  function read(k, d) {
    try { return JSON.parse(localStorage.getItem('aa.' + k)) || d; }
    catch (e) { return d; }
  }

  /* This script ships in the one site.js on every page; it serves only the
     reader's own page, which is marked by its panels. */
  if (!document.querySelector('[data-panel]')) return;

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
    return (window.AA ? AA.u('read.php', { work: b[0], c: b[1] })
                      : 'read.php?work=' + encodeURIComponent(b[0]) + '&c=' + encodeURIComponent(b[1]))
         + '#' + frag;
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

/* ===== read.js ===== */
/* The Abrahamic Library — the reader, for the static site.
 *
 * On the PHP site read.php built this page on the server. Here the shell is
 * already in read.html and this script fills the same markup from the packed
 * corpus: the chapter heading, the verses, the section headings, the notes
 * in the margin, the citation counts, and the compare link. The classes and
 * structure are the PHP page's own, so the stylesheet and study.js work
 * unchanged.
 */
(function () {
  'use strict';

  var reader = document.querySelector('[data-reader]');
  if (!reader) return;

  var q = AA.query();
  var id = q.work || '';
  var n = q.c || '1';

  var main = document.getElementById('main');

  function fail(title, lead, href, label) {
    while (main.firstChild) main.removeChild(main.firstChild);
    var d = document.createElement('div');
    d.className = 'wrap hero';
    d.innerHTML = '<h1></h1><p class="lead"></p><a class="btn" href="' +
      AA.e(href) + '"></a>';
    d.querySelector('h1').textContent = title;
    d.querySelector('.lead').textContent = lead;
    d.querySelector('a').textContent = label;
    main.appendChild(d);
    document.title = title + ' — The Abrahamic Library';
  }

  function fragFrom(html) {
    var t = document.createElement('template');
    t.innerHTML = html;
    return t.content;
  }

  AA.work(id).then(function (meta) {
    if (!meta) { fail('No such work', 'It may have been renamed. The library lists everything.', 'library.html', 'Open the library'); return; }
    return AA.chapter(id, n).then(function (ch) {
      if (!ch) { fail('No such chapter', 'The library lists everything the archive holds.', 'library.html', 'Open the library'); return; }
      render(meta, ch);
    });
  }).catch(function (err) {
    fail('No such chapter', 'The library lists everything the archive holds.', 'library.html', 'Open the library');
    if (window.console) console.error(err);
  });

  function render(meta, ch) {
    var others = null;
    var book = null;
    var cites = {};
    var cref = null;

    Promise.all([
      AA.editionsOf(meta).then(function (o) { others = o; }),
      AA.canonBook(id).then(function (b) { book = b; }),
      AA.canonRef(id, n).then(function (c) { cref = c; })
    ]).then(function () {
      if (book) {
        return AA.citationCounts(book.key, n).then(function (c) { cites = c; });
      }
    }).then(function () {
      paint(meta, ch, others, book, cites, cref);
    });
  }

  function paint(meta, ch, others, book, cites, cref) {
    var [prev, next] = AA.neighbours(meta, n);
    var title = ch.title || ('Chapter ' + n);
    var refBase = meta.title + ' ' + n;

    var hasSrc = false;
    (ch.verses || []).forEach(function (v) { if (!hasSrc && v.src) hasSrc = true; });
    if (!hasSrc) {
      (ch.blocks || []).forEach(function (b) { if (!hasSrc && b.s) hasSrc = true; });
    }

    /* The page's own data attributes, which the scripts read. */
    reader.dataset.work = id;
    reader.dataset.c = n;
    reader.dataset.title = meta.title;
    reader.dataset.religion = meta.religion;
    reader.dataset.canon = cref ? cref[0] : '';
    reader.dataset.canonCh = cref ? cref[1] : '';
    reader.dataset.verses = '1';

    var crumbs = document.querySelector('.crumbs');
    if (crumbs) {
      crumbs.innerHTML =
        '<a href="library.html">Library</a> &rsaquo; ' +
        '<a href="' + AA.u('library.php', { religion: meta.religion }) + '">' +
          AA.e(AA.religionName(meta.religion)) + '</a> &rsaquo; ' +
        '<a href="' + AA.u('work.php', { work: id }) + '">' + AA.e(meta.title) + '</a>';
    }

    var head = reader.querySelector('.reader-head');
    head.innerHTML = '<h1></h1><p class="sub"></p>';
    head.querySelector('h1').textContent = meta.title;
    var sub = title;
    if (meta.edition && meta.edition.translator) sub += ' \u00b7 ' + meta.edition.translator;
    head.querySelector('.sub').textContent = sub;

    /* The chapter's own meta blocks sit between the heading and the body,
       which is where the PHP page prints them. */
    var body = reader.querySelector('[data-body]');
    var scripture = body.querySelector('.scripture');

    var before = [];
    (ch.blocks || []).forEach(function (b) {
      if ((b.k || '') === 'meta') {
        before.push('<p class="chapter-meta">' + AA.e(b.t) + '</p>');
      }
    });
    var old = reader.querySelectorAll('.chapter-meta');
    for (var oi = 0; oi < old.length; oi++) old[oi].remove();
    if (before.length) {
      head.insertAdjacentHTML('afterend', before.join(''));
    }

    var notes = [];
    var headings = {};
    (ch.blocks || []).forEach(function (b) {
      if ((b.k || '') === 'h' && b.at !== undefined) {
        (headings[String(b.at)] = headings[String(b.at)] || []).push(b.t);
      }
    });

    var out = '';
    if (ch.verses && ch.verses.length) {
      ch.verses.forEach(function (v) {
        var vid = 'v' + String(v.n).replace(/[^0-9a-z]/gi, '');
        (v.notes || []).forEach(function (note) {
          notes.push({ ref: note.ref || '', text: note.text || '', anchor: vid });
        });
        (headings[String(v.n)] || []).forEach(function (h) {
          out += '<h3 class="head">' + AA.e(h) + '</h3>';
        });
        out += '<span class="v" id="' + AA.e(vid) + '"' +
          ' data-work="' + AA.e(id) + '" data-c="' + AA.e(n) + '" data-v="' + AA.e(v.n) + '"' +
          ' data-ref="' + AA.e(refBase + ':' + v.n) + '"' +
          (v.src ? ' data-src="' + AA.e(v.src) + '"' : '') + '>' +
          '<a class="vn" href="#' + AA.e(vid) + '" data-ref="' + AA.e(refBase + ':' + v.n) + '">' +
            AA.e(v.n) + '</a><span class="t">' + AA.e(v.text) + '</span>';
        var count = cites[String(v.n)];
        if (count) {
          out += '<a class="vcite" href="' +
            AA.e(AA.u('cited.php', { ref: book.key + '|' + n + '|' + v.n })) + '"' +
            ' title="' + count + ' works in this archive cite this verse">' +
            '\u2009' + count + '\u2009cite' + (count === 1 ? '' : 's') + '</a>';
        }
        out += '</span>';
      });
    } else {
      var pn = 1;
      (ch.blocks || []).forEach(function (b) {
        var kind = b.k || 'p';
        if (kind === 'h') {
          out += '<h3 class="head">' + AA.e(b.t) + '</h3>';
        } else if (kind !== 'meta') {
          out += '<p class="pb" id="p' + pn + '"' +
            ' data-work="' + AA.e(id) + '" data-c="' + AA.e(n) + '" data-v="p' + pn + '"' +
            (b.s ? ' data-src="' + AA.e(b.s) + '"' : '') +
            ' data-ref="' + AA.e(refBase) + ' \u00b6' + pn + '">' +
            '<span class="t">' + AA.e(b.t) + '</span></p>';
          pn++;
        }
      });
    }
    scripture.innerHTML = out;

    /* The two margins: the translator's notes, and the reader's own. */
    var aside = body.querySelector('.margin-a');
    if (notes.length) {
      var h = '<h3 class="margin-h">Notes on the text</h3>';
      notes.forEach(function (note) {
        h += '<div class="mnote" data-for="' + AA.e(note.anchor) + '">' +
          '<b>' + AA.e(note.ref) + '</b><span>' + AA.e(note.text) + '</span></div>';
      });
      aside.innerHTML = h;
      aside.hidden = false;
    } else {
      aside.innerHTML = '<h3 class="margin-h">Notes on the text</h3>';
      aside.hidden = true;
    }

    /* The compare link, only where other editions exist. */
    var tools = reader.querySelector('.reader-tools');
    var cmp = tools.querySelector('[data-compare-link]');
    if (others && others.length) {
      if (!cmp) {
        cmp = document.createElement('a');
        cmp.className = 'btn alt';
        cmp.setAttribute('data-compare-link', '');
        cmp.style.cssText = 'padding:.3rem .7rem;font-size:.8rem';
        cmp.textContent = 'Compare';
        var bar = tools.querySelector('[data-act="close"]');
        if (bar) tools.insertBefore(cmp, bar.closest('.vbar') || null);
        else tools.appendChild(cmp);
      }
      cmp.href = AA.u('compare.php', { work: id, c: n });
    } else if (cmp) {
      cmp.remove();
    }

    /* The pager. */
    var pager = reader.querySelector('.pager');
    pager.innerHTML =
      (prev !== null
        ? '<a rel="prev" href="' + AA.e(AA.u('read.php', { work: id, c: prev })) + '">&larr; ' + AA.e(prev) + '</a>'
        : '<span></span>') +
      '<a href="' + AA.u('work.php', { work: id }) + '">All chapters</a>' +
      (next !== null
        ? '<a rel="next" href="' + AA.e(AA.u('read.php', { work: id, c: next })) + '">' + AA.e(next) + ' &rarr;</a>'
        : '<span></span>');

    var foot = reader.querySelector('[data-reader-foot]');
    foot.innerHTML = AA.e((meta.edition && meta.edition.translation) || 'Public domain text') +
      '. ' + AA.e(AA.tierLabel(meta.edition && meta.edition.modernization)) +
      ' &mdash; <a href="about.html">what that means</a>.';
    foot.removeAttribute('data-reader-foot');

    document.title = meta.title + ' ' + n + ' — The Abrahamic Library';

    /* The shell is complete. study.js and wordstudy.js listen for this and
       take the page from here. */
    reader.dataset.painted = '1';
    var find = reader.querySelector('[data-find-work]');
    if (find) find.value = id;
    var mark = reader.querySelector('[data-bookmark]');
    if (mark) mark.setAttribute('data-bookmark', meta.title + ' ' + n);
    reader.dispatchEvent(new CustomEvent('aa:chapter', { bubbles: true }));
  }
})();

/* ===== compare.js ===== */
/* The Abrahamic Library — the comparison page, for the static site.
 *
 * compare.php put two or more editions of a chapter side by side on the
 * server. This draws the same markup in the browser from the query string:
 * "compare.html?work=quran-pickthall&c=1" reads like the PHP page did.
 */
(function () {
  'use strict';

  var q = AA.query();
  var id = q.work || '';
  var n = q.c || '1';
  var main = document.getElementById('main');
  if (!main || !main.querySelector('[data-compare-grid]')) return;   /* not the compare page */

  var crumbs = main.querySelector('.crumbs');
  var h1 = main.querySelector('.hero h1');
  var lead = main.querySelector('.hero .lead');
  var form = main.querySelector('[data-compare-form]');
  var choices = main.querySelector('[data-compare-choices]');
  var grid = main.querySelector('[data-compare-grid]');
  var pager = main.querySelector('.pager');

  AA.work(id).then(function (meta) {
    if (!meta) {
      document.title = 'No such work — The Abrahamic Library';
      h1.textContent = 'No such work';
      lead.textContent = 'It may have been renamed. The library lists everything.';
      crumbs.innerHTML = '<a href="library.html">Library</a>';
      return;
    }

    return AA.editionsOf(meta).then(function (available) {
      var chosen = q.with;
      var chosenIds = chosen == null ? null : (Array.isArray(chosen) ? chosen : [chosen]);

      var columns = [{ meta: meta, id: id }];
      var picks = [];
      available.forEach(function (o) {
        if (chosenIds === null || chosenIds.indexOf(o.id) !== -1) picks.push(o.id);
      });

      return Promise.all(picks.map(function (oid) {
        return AA.work(oid).then(function (m) {
          if (m) columns.push({ meta: m, id: oid });
        });
      })).then(function () {
        return AA.canonRef(id, n).then(function (cref) {
          var loads = columns.map(function (c) { return columnChapter(c, cref); });
          return Promise.all(loads).then(function (chapters) {
            paint(meta, available, chosenIds, columns, chapters, cref);
          });
        });
      });
    });
  });

  /* The whole Bibles do not number their chapters the same way after Esther
     and Daniel, so a column is asked for the chapter by its canonical
     reference, and skipped when it does not hold that book. */
  function columnChapter(col, cref) {
    var whole = ['kjv-bible', 'webu-bible', 'dr-bible'].indexOf(col.id) !== -1;
    if (col.id === id) return AA.chapter(col.id, n);
    if (whole) {
      if (cref === null) return AA.chapter(col.id, n);
      return AA.canonGlobal(col.id, cref[0], cref[1]).then(function (g) {
        return g !== null ? AA.chapter(col.id, g) : null;
      });
    }
    return AA.canonBook(col.id).then(function (book) {
      if (book !== null && cref !== null && book.key === cref[0]) {
        return AA.chapter(col.id, cref[1]);
      }
      return AA.chapter(col.id, n);
    });
  }

  function paint(meta, available, chosenIds, columns, chapters, cref) {
    document.title = meta.title + ' ' + n + ' compared — The Abrahamic Library';
    crumbs.innerHTML =
      '<a href="library.html">Library</a> &rsaquo; ' +
      '<a href="' + AA.u('work.php', { work: id }) + '">' + AA.e(meta.title) + '</a> &rsaquo; Comparing';
    h1.textContent = meta.title + ' ' + n;
    lead.textContent = columns.length + ' translations, verse by verse.';

    if (available.length) {
      form.hidden = false;
      form.querySelector('input[name="work"]').value = id;
      form.querySelector('input[name="c"]').value = n;
      choices.innerHTML = available.map(function (o) {
        var on = chosenIds === null || chosenIds.indexOf(o.id) !== -1;
        return '<label class="tag" style="padding:.4rem .7rem;text-transform:none;font-size:.82rem">' +
          '<input type="checkbox" name="with[]" value="' + AA.e(o.id) + '"' + (on ? ' checked' : '') + '> ' +
          AA.e(o.edition && o.edition.translator ? o.edition.translator : o.title) + '</label>';
      }).join(' ');
    }

    grid.innerHTML = columns.map(function (col, i) {
      var m = col.meta, cch = chapters[i];
      var head = AA.e((m.edition && m.edition.translator) || m.title) +
        (m.edition && m.edition.year
          ? ' <span class="muted small">&middot; ' + AA.e(String(m.edition.year)) + '</span>' : '');
      var inner;
      if (!cch) {
        inner = '<p class="muted small">This edition has no chapter ' + AA.e(n) + '.</p>';
      } else if (cch.verses && cch.verses.length) {
        inner = '<div class="scripture">' + cch.verses.map(function (v) {
          var vid = AA.e(col.id + '-v' + String(v.n).replace(/[^0-9a-z]/gi, ''));
          return '<span class="v" id="' + vid + '">' +
            '<a class="vn" href="#' + vid + '" data-ref="' +
              AA.e(m.title + ' ' + n + ':' + v.n) + '">' + AA.e(v.n) + '</a>' +
            AA.e(v.text) + '</span>';
        }).join('') + '</div>';
      } else {
        inner = '<div class="scripture">' + (cch.blocks || []).filter(function (b) {
          return (b.k || '') !== 'meta';
        }).map(function (b) {
          return '<p>' + AA.e(b.t) + '</p>';
        }).join('') + '</div>';
      }
      return '<section class="compare-col"><h3>' + head + '</h3>' + inner + '</section>';
    }).join('');

    var nb = AA.neighbours(meta, n);
    pager.innerHTML =
      (nb[0] !== null
        ? '<a rel="prev" href="' + AA.e(AA.u('compare.php', { work: id, c: nb[0] })) + '">&larr; ' + AA.e(nb[0]) + '</a>'
        : '<span></span>') +
      '<a href="' + AA.e(AA.u('read.php', { work: id, c: n })) + '">Read this one alone</a>' +
      (nb[1] !== null
        ? '<a rel="next" href="' + AA.e(AA.u('compare.php', { work: id, c: nb[1] })) + '">' + AA.e(nb[1]) + ' &rarr;</a>'
        : '<span></span>');
  }
})();

/* ===== cited.js ===== */
/* The Abrahamic Library — "every work that cites this verse".
 *
 * cited.php built this page from data/links on the server. Here the small
 * per-chapter citation files are fetched as needed, so the page costs one
 * request and nothing is shipped for the verses nobody looks at.
 */
(function () {
  'use strict';

  /* This script rides in the one site.js on every page, so it first makes
     sure it is on the page it serves: the "cited by" shell is marked, and
     nothing else is. */
  var main = document.getElementById('main');
  if (!main || !main.querySelector('[data-cited-ref]')) return;

  var q = AA.query();
  var ref = q.ref || '';
  var bits = ref.split('|');

  function notARef() {
    var d = document.createElement('div');
    d.className = 'wrap hero';
    d.innerHTML = '<h1>Not a reference</h1><a class="btn" href="library.html">Open the library</a>';
    while (main.firstChild) main.removeChild(main.firstChild);
    main.appendChild(d);
    document.title = 'Not a reference — The Abrahamic Library';
  }

  if (bits.length !== 3 || !/^[a-z0-9-]+$/.test(bits[0]) ||
      !/^\d+$/.test(bits[1]) || !/^\d+$/.test(bits[2])) {
    notARef();
    return;
  }

  var book = bits[0], chapterN = bits[1], verse = bits[2];

  AA.citedBy(ref).then(function (rows) {
    AA.linkBooks().then(function (books) {
      /* The verse itself, in whichever edition of the book is held. */
      var candidates = [];
      for (var wid in books) {
        if (books[wid][0] === book) candidates.push(wid);
      }
      var label = book.replace(/-/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); });
      var text = '', link = '';

      var chain = Promise.resolve();
      candidates.forEach(function (wid) {
        chain = chain.then(function () {
          if (text !== '') return;
          return AA.work(wid).then(function (meta) {
            if (!meta) return;
            return AA.chapter(wid, chapterN).then(function (ch) {
              (ch && ch.verses || []).forEach(function (v) {
                if (String(v.n) === verse && text === '') {
                  text = v.text;
                  label = books[wid][1];
                  link = AA.u('read.php', { work: wid, c: chapterN }) + '#v' + verse;
                }
              });
            });
          });
        });
      });

      chain.then(function () {
        paint(label, rows, text, link);
      });
    });
  });

  function paint(label, rows, text, link) {
    document.title = label + ' ' + chapterN + ':' + verse + ' — cited by — The Abrahamic Library';
    var count = rows.length;

    document.querySelector('[data-cited-count]').textContent =
      'Cited by ' + count + ' work' + (count === 1 ? '' : 's');
    document.querySelector('[data-cited-ref]').textContent =
      label + ' ' + chapterN + ':' + verse;

    var slot = document.querySelector('[data-cited-text]');
    if (text) {
      slot.innerHTML = '<blockquote class="cited-text">' + AA.e(text) + '</blockquote>' +
        '<p><a class="btn alt" href="' + AA.e(link) + '">Read it in place</a></p>';
    }

    var body = document.querySelector('[data-cited-body]');
    if (!rows.length) {
      body.innerHTML = '<section class="wrap"><p class="muted">Nothing in the archive cites this verse.</p></section>';
      return;
    }

    /* Grouped by religion, as the PHP page grouped them. */
    var byReligion = {};
    rows.forEach(function (r) { (byReligion[r.religion] = byReligion[r.religion] || []).push(r); });

    body.innerHTML = Object.keys(byReligion).map(function (religion) {
      var works = byReligion[religion];
      var list = works.map(function (w) {
        return '<a class="cite-row" href="' + AA.e(AA.u('work.php', { work: w.work })) + '">' +
          '<span class="cite-n">' + Number(w.n) + '</span>' +
          '<span class="cite-t">' + AA.e(w.title) + '</span></a>';
      }).join('');
      return '<section class="wrap" data-religion="' + AA.e(religion) + '">' +
        '<div class="section-head"><h2>' + AA.e(AA.religionName(religion)) + '</h2>' +
        '<span class="muted small">' + works.length + ' works</span></div>' +
        '<div class="cite-list">' + list + '</div></section>';
    }).join('');
  }
})();

/* ===== library.js ===== */
/* The Abrahamic Library — the library, for the static site.
 *
 * library.php rendered every view from the catalog on the server. This
 * draws the same markup — the same cards, the same section headings, the
 * same pagination — in the browser, from the same catalog, by way of the
 * query string:
 *
 *   library.html                        all three religions
 *   library.html?religion=judaism       one religion
 *   library.html?religion=judaism&section=torah       one section, paged
 *
 * One file answers all of it; the address is the view.
 */
(function () {
  'use strict';

  var PREVIEW = 12;    /* works shown per section on a religion page */
  var PER_PAGE = 60;   /* works per page on a section page */

  var q = AA.query();
  var wantR = q.religion || '';
  var wantS = q.section || '';
  var page = Math.max(1, parseInt(q.p || '1', 10) || 1);

  var root = document.querySelector('[data-library]');
  if (!root) return;                          /* not the library page */
  var crumbs = root.querySelector('[data-crumbs]');
  var title = root.querySelector('[data-library-title]');
  var lead = root.querySelector('[data-library-lead]');
  var count = root.querySelector('[data-library-count]');
  var body = root.querySelector('[data-library-body]');

  function card(w) {
    return '<a class="work-card" href="' + AA.e(AA.u('work.php', { work: w.id })) + '">' +
      '<b>' + AA.e(w.title) + '</b>' +
      (w.subtitle ? '<small>' + AA.e(w.subtitle) + '</small>' : '') +
      '<small>' +
        (w.borrowed_from
          ? '<span class="tag borrowed">also in ' + AA.e(AA.religionName(w.borrowed_from)) + '</span>' : '') +
        AA.num(w.stats && w.stats.chapters || 0) + ' chapters' +
        (w.edition && w.edition.translator ? ' &middot; ' + AA.e(w.edition.translator) : '') +
      '</small></a>';
  }

  function pagination(pages, current, params, label) {
    var from = Math.max(1, current - 3);
    var to = Math.min(pages, from + 6);
    var out = '<nav class="pagination" aria-label="' + label + '">';
    function link(p, text) {
      var merged = Object.assign({}, params, { p: p });
      return '<a href="' + AA.e(AA.u('library.php', merged)) + '">' + text + '</a>';
    }
    if (current > 1) out += link(current - 1, '&larr; Back');
    for (var i = from; i <= to; i++) {
      out += i === current ? '<span aria-current="page">' + i + '</span>' : link(i, String(i));
    }
    if (current < pages) out += link(current + 1, 'Next &rarr;');
    return out + '</nav>';
  }

  AA.catalog().then(function (cat) {
    var one = null;
    if (wantR) {
      cat.religions.forEach(function (r) { if (r.id === wantR) one = r; });
    }

    if (wantR && !one) {
      title.textContent = 'Nothing under that name';
      lead.textContent = 'The library holds Judaism, Christianity and Islam.';
      count.textContent = '';
      body.innerHTML = '<p><a class="btn" href="library.html">See all three</a></p>';
      document.title = 'Nothing under that name — The Abrahamic Library';
      return;
    }

    var section = null;
    if (one && wantS) {
      one.sections.forEach(function (s) { if (s.id === wantS) section = s; });
    }

    if (section) {
      document.querySelector('html').setAttribute('data-religion', one.id);
      document.title = section.name + ' — The Abrahamic Library';
      crumbs.hidden = false;
      crumbs.innerHTML =
        '<a href="library.html">Library</a> &rsaquo; ' +
        '<a href="' + AA.e(AA.u('library.php', { religion: one.id })) + '">' + AA.e(one.name) + '</a> &rsaquo; ' +
        AA.e(section.name);

      var works = section.works;
      var total = works.length;
      var pages = Math.max(1, Math.ceil(total / PER_PAGE));
      page = Math.min(page, pages);
      var slice = works.slice((page - 1) * PER_PAGE, page * PER_PAGE);

      title.textContent = section.name;
      lead.textContent = section.blurb;
      count.textContent = AA.num(total) + ' works' +
        (pages > 1 ? ' \u00b7 page ' + AA.num(page) + ' of ' + AA.num(pages) : '');

      body.innerHTML = '<div class="grid-works">' + slice.map(card).join('') + '</div>' +
        (pages > 1
          ? pagination(pages, page, { religion: one.id, section: section.id }, 'Pages')
          : '');
      return;
    }

    /* The whole library, or one religion. */
    if (one) {
      document.querySelector('html').setAttribute('data-religion', one.id);
      document.title = one.name + ' — The Abrahamic Library';
      crumbs.hidden = false;
      crumbs.innerHTML = '<a href="library.html">Library</a> &rsaquo; ' + AA.e(one.name);
    } else {
      document.title = 'The whole library — The Abrahamic Library';
    }

    title.textContent = one ? one.name : 'The whole library';
    lead.textContent = one ? one.blurb
      : 'Everything in the archive, arranged as each tradition arranges it.';
    var t = one ? one.totals : cat.totals;
    count.textContent = AA.num(t && t.works) + ' works \u00b7 ' +
      AA.num(t && t.chapters) + ' chapters \u00b7 ' + AA.num(t && t.words) + ' words';

    var out = '';

    if (!one) {
      /* The complete scriptures first: each translation whole, not a book
         at a time, as the PHP page orders them. */
      var wholeBibles = [];
      var wholeQurans = [];
      cat.religions.forEach(function (r) {
        r.sections.forEach(function (s) {
          s.works.forEach(function (w) {
            if (s.id === 'whole-bible') wholeBibles.push(w);
            else if (s.id === 'quran' && w.id.indexOf('quran-') === 0) wholeQurans.push(w);
          });
        });
      });
      if (wholeBibles.length) {
        out += '<div class="section-head"><h2>The Bible, complete</h2>' +
          '<p>Every book, with the Apocrypha, in one work each.</p></div>' +
          '<div class="grid-works">' + wholeBibles.map(card).join('') + '</div>';
      }
      if (wholeQurans.length) {
        out += '<div class="section-head"><h2>The Qur\u2019an, complete</h2>' +
          '<p>The whole scripture, in each translation that is free to reprint.</p></div>' +
          '<div class="grid-works">' + wholeQurans.map(card).join('') + '</div>';
      }
    }

    (one ? [one] : cat.religions).forEach(function (r) {
      if (!one) {
        out += '<div class="section-head">' +
          '<h2><a href="' + AA.e(AA.u('library.php', { religion: r.id })) + '">' +
            AA.e(r.name) + '</a></h2>' +
          '<p>' + AA.num(r.totals.works) + ' works</p></div>';
      }
      r.sections.forEach(function (s) {
        var items = s.works;
        if (!one) {
          if (s.id === 'whole-bible') return;
          if (s.id === 'quran') {
            items = items.filter(function (w) { return w.id.indexOf('quran-') !== 0; });
            if (!items.length) return;
          }
        }
        out += '<div class="section-head"><h2>' +
          '<a href="' + AA.e(AA.u('library.php', { religion: r.id, section: s.id })) + '">' +
            AA.e(s.name) + '</a></h2>' +
          '<p>' + AA.e(s.blurb) + '</p></div>' +
          '<div class="grid-works">' + items.slice(0, PREVIEW).map(card).join('') + '</div>';
        if (items.length > PREVIEW) {
          out += '<p style="margin:.7rem 0 0"><a href="' +
            AA.e(AA.u('library.php', { religion: r.id, section: s.id })) + '">All ' +
            AA.num(items.length) + ' in ' + AA.e(s.name) + ' &rarr;</a></p>';
        }
      });
    });

    body.innerHTML = out;
  });
})();

/* ===== work.js ===== */
/* The Abrahamic Library — one work's page, for the static site.
 *
 * work.php built this from the work's metadata on the server. This draws
 * the same page in the browser: what the edition is, its chapters or named
 * sections (paged the same way), and the other translations of the book.
 */
(function () {
  'use strict';

  var q = AA.query();
  var id = q.work || '';

  var root = document.querySelector('[data-work-page]');
  if (!root) return;                          /* not a work's page */
  var crumbs = root.querySelector('[data-crumbs]');
  var h1 = root.querySelector('[data-work-title]');
  var subtitle = root.querySelector('[data-work-subtitle]');
  var start = root.querySelector('[data-work-start]');
  var compare = root.querySelector('[data-work-compare]');
  var head = root.querySelector('[data-contents-heading]');
  var countLine = root.querySelector('[data-contents-count]');
  var contents = root.querySelector('[data-contents]');
  var pager = root.querySelector('[data-contents-pager]');
  var facts = root.querySelector('[data-facts]');
  var alsoWrap = root.querySelector('[data-also-wrap]');
  var also = root.querySelector('[data-also]');
  var tier = root.querySelector('[data-work-tier]');

  function fail() {
    h1.textContent = 'No such work';
    subtitle.hidden = false;
    subtitle.textContent = 'It may have been renamed. The library lists everything.';
    root.querySelector('.actions').innerHTML =
      '<a class="btn" href="library.html">Open the library</a>';
    document.title = 'No such work — The Abrahamic Library';
  }

  AA.work(id).then(function (meta) {
    if (!meta) { fail(); return; }
    return AA.editionsOf(meta).then(function (others) {
      paint(meta, others);
    });
  }).catch(function () { fail(); });

  function paint(meta, others) {
    document.title = meta.title + ' — The Abrahamic Library';
    document.querySelector('html').setAttribute('data-religion', meta.religion);

    crumbs.innerHTML =
      '<a href="library.html">Library</a> &rsaquo; ' +
      '<a href="' + AA.e(AA.u('library.php', { religion: meta.religion })) + '">' +
        AA.e(AA.religionName(meta.religion)) + '</a> &rsaquo; ' +
      AA.e(meta.section_name || '');

    h1.textContent = meta.title;
    if (meta.subtitle) {
      subtitle.hidden = false;
      subtitle.textContent = meta.subtitle;
    }

    /* A chapter entry is [number, title, verse count, bundle, offset, length]. */
    var chapters = meta.chapters || [];
    var first = chapters.length ? chapters[0][0] : '1';
    start.href = AA.u('read.php', { work: id, c: first });
    if (others.length) {
      compare.hidden = false;
      compare.href = AA.u('compare.php', { work: id, c: first });
    }

    /* A Fathers volume can run to a thousand named sections, so the
       contents page pages rather than printing all of them at once. */
    var named = chapters.some(function (c) {
      return c[1] && !/^Chapter /.test(c[1]);
    });
    var perPage = named ? 60 : 400;
    var total = chapters.length;
    var pages = Math.max(1, Math.ceil(total / perPage));
    var page = Math.min(Math.max(1, parseInt(q.p || '1', 10) || 1), pages);
    var slice = chapters.slice((page - 1) * perPage, page * perPage);

    head.textContent = named ? 'Contents' : 'Chapters';
    countLine.textContent = AA.num(total) + ' in all' +
      (pages > 1 ? ' \u00b7 page ' + AA.num(page) + ' of ' + AA.num(pages) : '');

    if (named) {
      contents.innerHTML = '<div class="grid-works">' + slice.map(function (c) {
        return '<a class="work-card" href="' + AA.e(AA.u('read.php', { work: id, c: c[0] })) + '">' +
          '<b>' + AA.e(c[1] || c[0]) + '</b>' +
          '<small>' + (c[2] ? AA.num(c[2]) + ' verses' : 'Section ' + AA.e(c[0])) + '</small>' +
          '</a>';
      }).join('') + '</div>';
    } else {
      contents.innerHTML = '<div class="chapters">' + slice.map(function (c) {
        return '<a href="' + AA.e(AA.u('read.php', { work: id, c: c[0] })) + '">' + AA.e(c[0]) + '</a>';
      }).join('') + '</div>';
    }

    if (pages > 1) {
      var from = Math.max(1, page - 3);
      var to = Math.min(pages, from + 6);
      var out = '<nav class="pagination" aria-label="Contents pages">';
      function link(p, text) {
        return '<a href="' + AA.e(AA.u('work.php', { work: id, p: p })) + '">' + text + '</a>';
      }
      if (page > 1) out += link(page - 1, '&larr; Back');
      for (var i = from; i <= to; i++) {
        out += i === page ? '<span aria-current="page">' + i + '</span>' : link(i, String(i));
      }
      if (page < pages) out += link(page + 1, 'Next &rarr;');
      pager.innerHTML = out + '</nav>';
    }

    var ed = meta.edition || {};
    var rows = '';
    if (ed.translation) rows += '<dt>Translation</dt><dd>' + AA.e(ed.translation) + '</dd>';
    if (ed.translator) rows += '<dt>Translator</dt><dd>' + AA.e(ed.translator) + '</dd>';
    if (ed.year) rows += '<dt>Published</dt><dd>' + AA.e(String(ed.year)) + '</dd>';
    rows += '<dt>English</dt><dd>' + AA.e(AA.tierLabel(ed.modernization)) + '</dd>';
    rows += '<dt>Length</dt><dd>' + AA.num(meta.stats && meta.stats.chapters) + ' chapters, ' +
      AA.num(meta.stats && meta.stats.words) + ' words</dd>';
    var rights = meta.rights || {};
    rows += '<dt>Rights</dt><dd>' + AA.e(rights.statement || 'Public domain.') +
      (rights.source_url
        ? '<br><a href="' + AA.e(rights.source_url) + '" rel="noopener nofollow">Source</a>' : '') +
      '</dd>';
    facts.innerHTML = rows;

    if (others.length) {
      alsoWrap.hidden = false;
      also.innerHTML = others.map(function (o) {
        return '<a href="' + AA.e(AA.u('work.php', { work: o.id })) + '">' +
          AA.e((o.edition && o.edition.translator) || o.id) + '</a>';
      }).join('');
    }

    tier.innerHTML = AA.e(AA.tierLabel(ed.modernization)) +
      '. <a href="about.html">What that changed</a>.';
  }
})();

/* ===== planpage.js ===== */
/* The Abrahamic Library — one reading plan, for the static site.
 *
 * plan.php rendered the days from data/plans.json on the server. This
 * draws the same list — day, title, and a link per reading — in the
 * browser. The ticks are assets/plan.js's business and stay in the
 * reader's own storage.
 */
(function () {
  'use strict';

  var q = AA.query();
  var id = q.id || '';

  if (!document.querySelector('[data-plan-name]')) return;   /* not a plan page */

  AA.plan(id).then(function (plan) {
    if (!plan) {
      document.title = 'No such plan — The Abrahamic Library';
      document.querySelector('h1').textContent = 'No such plan';
      document.querySelector('.lead').textContent = 'The plans page lists every one.';
      document.querySelector('.actions').innerHTML =
        '<a class="btn" href="plans.html">See the plans</a>';
      return;
    }

    document.title = plan.name + ' — The Abrahamic Library';
    if (plan.religion) {
      document.querySelector('html').setAttribute('data-religion', plan.religion);
    }

    document.querySelector('[data-plan-name]').textContent = plan.name;
    document.querySelector('[data-plan-blurb]').textContent = plan.blurb;
    document.querySelector('[data-plan]').setAttribute('data-plan', plan.id);

    document.querySelector('[data-plan-days]').innerHTML = plan.days.map(function (d, i) {
      return '<li class="plan-day" data-day="' + i + '" id="day' + (i + 1) + '">' +
        '<label class="plan-tick">' +
          '<input type="checkbox" data-plan-done="' + i + '">' +
          '<span class="sr">Mark day ' + (i + 1) + ' as read</span>' +
        '</label>' +
        '<div class="plan-body">' +
          '<p class="plan-n">Day ' + (i + 1) + '</p>' +
          '<h2>' + AA.e(d.title) + '</h2>' +
          '<p class="plan-links">' + d.readings.map(function (r) {
            return '<a href="' + AA.e(AA.u('read.php', { work: r.work, c: r.c })) + '">' +
              AA.e(r.title + ' ' + r.c) + '</a>';
          }).join(' ') + '</p>' +
        '</div></li>';
    }).join('');

    /* The shell hides the bar until a plan is here to measure; plan.js
       paints it as soon as it runs, which is after this. */
    document.dispatchEvent(new CustomEvent('aa:plan'));
  });
})();

/* ===== searchpage.js ===== */
/* The Abrahamic Library — search, for the static site.
 *
 * The PHP site answered from three places. Here the same three answers are
 * built in the browser:
 *
 *   - a reference ("John 3:16") jumps to the verse in the KJV, from the
 *     small book/chapter map in data/kjv_search.json;
 *   - a word or phrase searches the whole library through the pre-built
 *     index under data/search/;
 *   - anything else matches the titles of every work in the catalog.
 *
 * The index is sharded and the manifest names the first term of each shard,
 * so a query reads the shard that holds its term and nothing else.
 */
(function () {
  'use strict';

  /* The search index lives in the data bundles; each shard is fetched by
     its own byte range, so a query transfers one shard. */
  var INDEX = 'data/bundle.json.gz';
  function part(name) { return AA.part(name); }
  var PER_PAGE = 25;

  var q = AA.query();
  var text = (q.q || '').trim();
  var rel = q.religion || '';
  var sec = q.section || '';
  var workId = q.work || '';
  var page = Math.max(1, parseInt(q.p || '1', 10) || 1);

  var main = document.getElementById('main');
  var results = main && main.querySelector('[data-search-results]');
  if (!results) return;                     /* not the search page */
  var hint = main.querySelector('[data-search-hint]');
  var progress = main.querySelector('[data-search-progress]');
  var input = main.querySelector('#q');
  if (input) input.value = text;

  document.title = (text ? 'Search: ' + text : 'Search') + ' — The Abrahamic Library';

  AA.catalog().then(function (cat) {
    var select = main.querySelector('[data-religion-select]');
    if (!select) return;
    cat.religions.forEach(function (r) {
      var o = document.createElement('option');
      o.value = r.id;
      o.textContent = r.name;
      if (r.id === rel) o.selected = true;
      select.appendChild(o);
    });
  });

  if (text === '') { hint.hidden = false; return; }
  hint.hidden = true;

  /* ---------- shared state ---------- */

  var manifestP = null;
  var unitsP = null;

  function manifest() {
    if (!manifestP) manifestP = part('search/manifest').then(function (t) { return JSON.parse(t); });
    return manifestP;
  }

  function units() {
    if (!unitsP) {
      unitsP = part('search/units').then(function (t) {
        return t.split('\n');
      });
    }
    return unitsP;
  }

  /* ---------- a reference ---------- */

  var ALIASES = {
    gen: 'Genesis', genesis: 'Genesis', exo: 'Exodus', exod: 'Exodus', exodus: 'Exodus',
    lev: 'Leviticus', leviticus: 'Leviticus', num: 'Numbers', numbers: 'Numbers',
    deut: 'Deuteronomy', deu: 'Deuteronomy', deuteronomy: 'Deuteronomy',
    josh: 'Joshua', joshua: 'Joshua', judg: 'Judges', judges: 'Judges', ruth: 'Ruth',
    '1 sam': '1 Samuel', '1 samuel': '1 Samuel', '2 sam': '2 Samuel', '2 samuel': '2 Samuel',
    '1 kgs': '1 Kings', '1 kings': '1 Kings', '2 kgs': '2 Kings', '2 kings': '2 Kings',
    '1 chr': '1 Chronicles', '1 chronicles': '1 Chronicles',
    '2 chr': '2 Chronicles', '2 chronicles': '2 Chronicles',
    ezra: 'Ezra', neh: 'Nehemiah', nehemiah: 'Nehemiah', esther: 'Esther', job: 'Job',
    ps: 'Psalms', psa: 'Psalms', psalm: 'Psalms', psalms: 'Psalms',
    prov: 'Proverbs', proverbs: 'Proverbs', eccl: 'Ecclesiastes', ecclesiastes: 'Ecclesiastes',
    song: 'Song of Solomon', 'song of solomon': 'Song of Solomon',
    isa: 'Isaiah', isaiah: 'Isaiah', jer: 'Jeremiah', jeremiah: 'Jeremiah',
    lam: 'Lamentations', lamentations: 'Lamentations', ezek: 'Ezekiel', ezekiel: 'Ezekiel',
    dan: 'Daniel', daniel: 'Daniel', hos: 'Hosea', hosea: 'Hosea', joel: 'Joel', amos: 'Amos',
    obad: 'Obadiah', obadiah: 'Obadiah', jonah: 'Jonah', mic: 'Micah', micah: 'Micah',
    nah: 'Nahum', nahum: 'Nahum', hab: 'Habakkuk', habakkuk: 'Habakkuk',
    zeph: 'Zephaniah', zephaniah: 'Zephaniah', hag: 'Haggai', haggai: 'Haggai',
    zech: 'Zechariah', zechariah: 'Zechariah', mal: 'Malachi', malachi: 'Malachi',
    matt: 'Matthew', matthew: 'Matthew', mark: 'Mark', luke: 'Luke', john: 'John',
    acts: 'Acts', rom: 'Romans', romans: 'Romans', '1 cor': '1 Corinthians',
    '1 corinthians': '1 Corinthians', '2 cor': '2 Corinthians', '2 corinthians': '2 Corinthians',
    gal: 'Galatians', galatians: 'Galatians', eph: 'Ephesians', ephesians: 'Ephesians',
    phil: 'Philippians', philippians: 'Philippians', col: 'Colossians', colossians: 'Colossians',
    '1 thess': '1 Thessalonians', '1 thessalonians': '1 Thessalonians',
    '2 thess': '2 Thessalonians', '2 thessalonians': '2 Thessalonians',
    '1 tim': '1 Timothy', '1 timothy': '1 Timothy', '2 tim': '2 Timothy', '2 timothy': '2 Timothy',
    titus: 'Titus', philem: 'Philemon', philemon: 'Philemon', heb: 'Hebrews', hebrews: 'Hebrews',
    james: 'James', '1 pet': '1 Peter', '1 peter': '1 Peter', '2 pet': '2 Peter',
    '2 peter': '2 Peter', '1 john': '1 John', '2 john': '2 John', '3 john': '3 John',
    jude: 'Jude', rev: 'Revelation', revelation: 'Revelation',
    tobit: 'Tobit', judith: 'Judith', wisdom: 'Wisdom', sirach: 'Sirach',
    ecclesiasticus: 'Sirach', baruch: 'Baruch', '1 esdras': '1 Esdras', '2 esdras': '2 Esdras',
    '1 macc': '1 Maccabees', '1 maccabees': '1 Maccabees',
    '2 macc': '2 Maccabees', '2 maccabees': '2 Maccabees'
  };

  function findRef() {
    var m = /^([A-Za-z0-9 .]+?)\s*(\d+)(?::(\d+))?$/.exec(text);
    if (!m) return Promise.resolve(null);
    var name = m[1].toLowerCase().trim();
    return part('kjv_search').then(function (t) { var idx = JSON.parse(t);
      var book = ALIASES[name] || null;
      if (!book) {
        Object.keys(idx.books).forEach(function (b) {
          if (b.toLowerCase() === name) book = b;
        });
      }
      if (!book) return null;
      var file = null;
      (idx.books[book] || []).forEach(function (pair) {
        if (pair[0] === parseInt(m[2], 10)) file = pair[1];
      });
      if (file === null) return null;
      return { book: book, ch: parseInt(m[2], 10),
               vs: m[3] !== undefined ? parseInt(m[3], 10) : null, file: file };
    });
  }

  function showRef(ref) {
    return AA.chapter('kjv-bible', ref.file).then(function (ch) {
      var verse = null;
      if (ref.vs !== null) {
        (ch && ch.verses || []).forEach(function (v) {
          if (parseInt(v.n, 10) === ref.vs) verse = v;
        });
      }
      var heading = ref.book + ' ' + ref.ch + (ref.vs !== null ? ':' + ref.vs : '');
      var html = '<section class="wrap"><div class="section-head"><h2>' + AA.e(heading) + '</h2>' +
        '<a class="more" href="' + AA.e(AA.u('read.php', { work: 'kjv-bible', c: ref.file })) +
        '">Open chapter &rarr;</a></div>';
      if (verse) {
        html += '<div class="hit"><a class="ref" href="' +
          AA.e(AA.u('read.php', { work: 'kjv-bible', c: ref.file })) + '#v' + AA.e(verse.n) + '">' +
          AA.e(heading) + '</a><p>' + AA.e(verse.text) + '</p></div>';
      } else {
        html += '<p class="muted">That chapter is there; pick a verse to land on it.</p>';
      }
      results.innerHTML = html + '</section>';
    });
  }

  /* ---------- a word or phrase ---------- */

  function shardOf(term, first) {
    var lo = 0, hi = first.length - 1;
    while (lo < hi) {
      var mid = (lo + hi + 1) >> 1;
      if (first[mid] <= term) lo = mid;
      else hi = mid - 1;
    }
    return lo;
  }

  function decode(b64) {
    var bin = atob(b64);
    var out = new Map();
    var i = 0, uid = 0;
    while (i < bin.length) {
      var shift = 0, n = 0, b;
      do { b = bin.charCodeAt(i++); n |= (b & 0x7f) << shift; shift += 7; } while (b & 0x80);
      uid += n;
      shift = 0; n = 0;
      do { b = bin.charCodeAt(i++); n |= (b & 0x7f) << shift; shift += 7; } while (b & 0x80);
      out.set(uid, n);
    }
    return out;
  }

  /* The index folds accents away (FTS5's unicode61 did), so a query that
     has them must be folded the same way or "Israël" would never match. */
  function foldAndStem(word) {
    var plain = word.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^A-Za-z0-9]/g, '');
    return plain ? window.AAPorter(plain) : '';
  }

  function wordSearch() {
    var stems = text.toLowerCase().split(/\s+/).filter(Boolean)
      .map(foldAndStem)
      .filter(Boolean);
    if (!stems.length) { none(); return; }

    progress.hidden = false;
    progress.textContent = 'Searching…';

    Promise.all([manifest(), units()]).then(function (both) {
      var m = both[0], unitLines = both[1];
      var cache = {};
      return Promise.all(stems.map(function (s) {
        var shard = shardOf(s, m.first);
        if (!cache[shard]) cache[shard] = part('search/w' + shard).then(function (t) { return JSON.parse(t); });
        return cache[shard].then(function (map) {
          return map[s] ? decode(map[s]) : null;
        });
      })).then(function (sets) {
        if (sets.indexOf(null) !== -1) { progress.hidden = true; none(); return; }
        var hits = intersect(sets);
        return render(m, unitLines, hits);
      });
    }).catch(function (err) {
      progress.hidden = true;
      progress.textContent = 'The search index could not be read: ' + err.message;
    });
  }

  /* Units present in every set, with the total occurrences of the terms. */
  function intersect(sets) {
    var smallest = sets[0];
    sets.forEach(function (s) { if (s.size < smallest.size) smallest = s; });
    var rest = sets.filter(function (s) { return s !== smallest; });
    var out = [];
    smallest.forEach(function (tf, uid) {
      var total = tf;
      for (var i = 0; i < rest.length; i++) {
        var n = rest[i].get(uid);
        if (n === undefined) return;
        total += n;
      }
      out.push([uid, total]);
    });
    return out;
  }

  function render(m, unitLines, hits) {
    var byId = {};
    m.order.forEach(function (w) { byId[w.id] = w; });

    /* In a work, or a religion, or a section, keep only those hits. */
    if (workId || rel || sec) {
      hits = hits.filter(function (h) {
        var row = unitLines[h[0]];
        if (!row) return false;
        var wid = row.slice(0, row.indexOf('|'));
        if (workId) return wid === workId;
        var w = byId[wid];
        if (!w) return false;
        if (rel && w.religion !== rel) return false;
        if (sec && w.section !== sec) return false;
        return true;
      });
    }

    var total = hits.length;
    var pages = Math.max(1, Math.ceil(total / PER_PAGE));
    page = Math.min(page, pages);
    var slice = hits.slice((page - 1) * PER_PAGE, page * PER_PAGE);

    if (!total) { progress.hidden = true; none(); return; }

    /* The chapter each hit is in, so the snippet is the real text. */
    var wanted = {};
    slice.forEach(function (h) {
      var bits = unitLines[h[0]].split('|');
      wanted[bits[0] + '|' + bits[1]] = true;
    });

    Promise.all(Object.keys(wanted).map(function (key) {
      var bits = key.split('|');
      return AA.chapter(bits[0], bits[1]).then(function (ch) { return [key, ch]; })
        .catch(function () { return [key, null]; });
    })).then(function (loaded) {
      progress.hidden = true;
      var chapters = {};
      loaded.forEach(function (pair) { chapters[pair[0]] = pair[1]; });
      paint(m, byId, unitLines, slice, total, pages, chapters);
    });
  }

  function paint(m, byId, unitLines, slice, total, pages, chapters) {
    var rows = slice.map(function (h) {
      var bits = unitLines[h[0]].split('|');
      var wid = bits[0], chap = bits[1], unit = bits[2];
      var meta = byId[wid];
      var ch = chapters[wid + '|' + chap];
      var body = '';
      if (ch) {
        if (unit.charAt(0) === 'p') {
          var blocks = (ch.blocks || []).filter(function (b) { return (b.k || '') !== 'meta'; });
          var i = parseInt(unit.slice(1), 10) - 1;
          body = blocks[i] ? blocks[i].t : '';
        } else {
          (ch.verses || []).forEach(function (v) {
            if (String(v.n) === String(unit)) body = v.text;
          });
        }
      }
      var frag = unit.charAt(0) === 'p' ? unit : 'v' + unit.replace(/[^0-9a-z]/gi, '');
      var label = (meta ? meta.title : wid) + ' ' + chap +
        (unit.charAt(0) === 'p' ? '' : ':' + unit);
      return '<div class="hit">' +
        '<a class="ref" href="' + AA.e(AA.u('read.php', { work: wid, c: chap })) + '#' + AA.e(frag) + '">' +
          AA.e(label) + '</a>' +
        (meta ? '<span class="where">' + AA.e(AA.religionName(meta.religion)) + '</span>' : '') +
        '<p>' + snippetOf(body) + '</p></div>';
    }).join('');

    var head = '<div class="section-head"><h2>' +
      (workId ? 'In ' + AA.e((byId[workId] || {}).title || workId) : 'Across the library') +
      '</h2><p>' + AA.num(total) + ' match' + (total === 1 ? '' : 'es') +
      ' for &ldquo;' + AA.e(text) + '&rdquo;</p></div>';

    var pagination = '';
    if (pages > 1) {
      var base = { q: text, religion: rel, section: sec, work: workId };
      function link(p, label) {
        var params = { q: base.q, religion: base.religion, section: base.section,
                       work: base.work, p: p };
        return '<a href="' + AA.e(AA.u('search.php', params)) + '">' + label + '</a>';
      }
      var from = Math.max(1, page - 3);
      var to = Math.min(pages, from + 6);
      pagination = '<nav class="pagination" aria-label="Result pages">';
      if (page > 1) pagination += link(page - 1, '&larr; Back');
      for (var i = from; i <= to; i++) {
        pagination += i === page ? '<span aria-current="page">' + i + '</span>'
                                 : link(i, String(i));
      }
      if (page < pages) pagination += link(page + 1, 'Next &rarr;');
      pagination += '</nav>';
    }

    results.innerHTML = '<section class="wrap">' + head + rows + pagination + '</section>';
  }

  /* The words of the query, marked in the text around them. */
  function snippetOf(body) {
    if (!body) return '';
    var words = text.split(/\s+/).filter(Boolean)
      .map(function (w) { return w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); });
    var re = new RegExp('(' + words.join('|') + ')', 'i');
    var hit = re.exec(body);
    var start = hit && hit.index > 80 ? hit.index - 60 : 0;
    var slice = body.slice(start, start + 280);
    if (start > 0) slice = '\u2026' + slice;
    var esc = AA.e(slice);
    return esc.replace(new RegExp('(' + words.join('|') + ')', 'gi'), '<mark>$1</mark>');
  }

  function none() {
    results.innerHTML = '<section class="wrap"><p class="lead">Nothing matched &ldquo;' +
      AA.e(text) + '&rdquo;. Try a book name, a reference, or a single word.</p></section>';
  }

  findRef().then(function (ref) {
    if (ref) return showRef(ref);
    return wordSearch();
  });
})();

/* ===== strongspage.js ===== */
/* The Abrahamic Library — the word study, for the static site.
 *
 * strongs.php answered from data/strongs.json and data/wordstudy.json on
 * the server. This asks the same files the same three ways: by number
 * (H430, G26), by transliterated word (agape, shalom), and — the point of
 * the page — by English word, where one English word stands for several
 * Hebrew or Greek ones.
 */
(function () {
  'use strict';

  var q = AA.query();
  var term = (q.q || '').trim();
  var answer = document.querySelector('[data-strongs-answer]');
  var body = document.querySelector('[data-strongs-body]');
  if (!answer || !body) return;              /* not the word-study page */
  var input = document.querySelector('#q');
  if (input) input.value = term;

  document.title = (term ? 'Word study: ' + term : 'Word study') + ' — The Abrahamic Library';

  var ws = null;

  function wordstudy() {
    if (!ws) ws = AA.wordstudy();
    return ws;
  }

  function lang(r) { return r === 'hebrew' ? 'Hebrew' : 'Greek'; }
  function rel(r) { return r === 'hebrew' ? 'judaism' : 'christianity'; }

  if (term === '') {
    wordstudy().then(function (d) {
      var box = document.querySelector('[data-strongs-samples]');
      box.innerHTML = (d.samples || []).slice(0, 12).map(function (w) {
        return '<a class="chip" href="?q=' + encodeURIComponent(w) + '">' + AA.e(w) + '</a>';
      }).join('');
    });
    return;
  }

  /* A guided word study, when the term names one. */
  wordstudy().then(function (d) {
    var fam = null;
    (d.families || []).forEach(function (f) {
      if (String(f.term).toLowerCase().trim() === term.toLowerCase().trim()) fam = f;
    });
    if (fam) return showFamily(fam, d);
    return plainLookup();
  });

  /* ---------- a family: several words behind one English one ---------- */

  function showFamily(fam, d) {
    answer.hidden = true;
    var cards = (fam.entries || []).map(function (id) {
      return AA.strongsEntry(id).then(function (x) {
        if (!x) return '';
        var plain = (fam.words && fam.words[id] && fam.words[id].plain) || '';
        return '<article class="lex plain" data-r="' + AA.e(rel(x.lang)) + '">' +
          '<p class="lex-head">' +
            '<a class="lex-id" href="' + AA.e(AA.u('strongs.php', { q: id })) + '">' + AA.e(id) + '</a>' +
            '<b class="lex-word">' + AA.e(String(x.word).toLowerCase()) + '</b>' +
            '<span class="muted small">' + lang(x.lang) + '</span></p>' +
          (plain ? '<p class="lex-plain">' + AA.e(plain) + '</p>' : '') +
          '<p class="lex-kjv"><span>King James renders it</span> ' + AA.e(x.kjv) + '</p></article>';
      });
    });
    Promise.all(cards).then(function (html) {
      body.innerHTML = '<section class="wrap">' +
        '<p class="eyebrow">A guided word study</p>' +
        '<h2 class="fam-q">' + AA.e(fam.question) + '</h2>' +
        '<p class="fam-line">' + AA.e(fam.line) + '</p>' +
        '<div class="fam">' + html.join('') + '</div></section>';
    });
  }

  /* ---------- a number, a word, or an English term ---------- */

  function plainLookup() {
    var m = /^([HGhg])\s*(\d{1,4})$/.exec(term);
    if (m) {
      var id = m[1].toUpperCase() + m[2];
      return AA.strongsEntry(id).then(function (x) {
        if (!x) { sayNone(); return; }
        answerLead('Strong\u2019s number <strong>' + AA.e(term) + '</strong>. ' +
          'The entry itself &mdash; the Hebrew/Greek word, how to say it, and what ' +
          'it means &mdash; is below; the King James line shows the English the ' +
          'translators chose for it.', 'lead muted small');
        showEntries([Object.assign({ id: id }, x)], 'number');
      });
    }

    var word = term.toLowerCase().replace(/[^A-Za-z'-]/g, '');
    if (!word) { sayNone(); return; }

    AA.strongsByEnglish(word).then(function (entries) {
      if (entries.length) {
        answerLead(entries.length + ' Hebrew and Greek words behind <strong>' +
          AA.e(term) + '</strong>. They are grouped below by what they actually mean ' +
          '&mdash; English flattens them into one, but they are not one thing.', 'lead');
        return showEntries(entries, 'english');
      }
      return AA.strongsByWord(word).then(function (byWord) {
        if (byWord.length) {
          answerLead(byWord.length + ' entries match <strong>' + AA.e(term) + '</strong>.', 'lead');
          return showEntries(byWord, 'word');
        }
        sayNone();
      });
    });
  }

  function answerLead(html, cls) {
    answer.hidden = false;
    answer.innerHTML = '<p class="' + cls + '">' + html + '</p>';
  }

  function sayNone() {
    answer.hidden = false;
    answer.innerHTML = '<p class="lead">Nothing in either dictionary answers to that.</p>';
  }

  function showEntries(entries, mode) {
    return wordstudy().then(function (d) {
      var plain = {};
      (d.families || []).forEach(function (f) {
        Object.keys(f.words || {}).forEach(function (id) {
          if (f.words[id].plain) plain[id] = f.words[id].plain;
        });
      });
      var cards = entries.map(function (x) {
        return '<article class="lex plain" data-r="' + AA.e(rel(x.lang)) + '">' +
          '<p class="lex-head">' +
            '<a class="lex-id" href="' + AA.e(AA.u('strongs.php', { q: x.id })) + '">' + AA.e(x.id) + '</a>' +
            '<b class="lex-word">' + AA.e(String(x.word).toLowerCase()) + '</b>' +
            (mode === 'english' && x.rank
              ? '<span class="lex-rank" title="How often the KJV used this word for the English term">used ' +
                AA.e(x.rank) + ' &times;</span>' : '') +
            '<span class="muted small">' + lang(x.lang) + '</span></p>' +
          (plain[x.id] ? '<p class="lex-plain">' + AA.e(plain[x.id]) + '</p>' : '') +
          '<p class="lex-sense">' + AA.e(x.sense) + '</p>' +
          (x.kjv ? '<p class="lex-kjv"><span>King James renders it</span> ' + AA.e(x.kjv) + '</p>' : '') +
          '</article>';
      });
      body.innerHTML = '<section class="wrap"><div class="fam">' + cards.join('') + '</div></section>';
    });
  }
})();
