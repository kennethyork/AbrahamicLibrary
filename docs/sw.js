/* The Abrahamic Library — service worker.
 *
 * What this can and cannot do is worth stating plainly. The corpus is
 * gigabytes of JSON; none of that is going onto a phone. What is kept here
 * is the shell — the stylesheet, the scripts, the offline page — and every
 * chapter you have actually opened, plus any a reading plan was asked to
 * save. That is the offline people use.
 */
var VERSION = 'aa-v3';
var SHELL   = VERSION + '-shell';
var PAGES   = VERSION + '-pages';

var PRECACHE = [
  'offline.html',
  'index.html',
  'library.html',
  'read.html',
  'search.html',
  'assets/style.css',
  'assets/site.js',
  'assets/icons/icon-192.png',
  'assets/icons/icon-512.png'
];

/* A page of the library is a file (library.html) or a reading page drawn
   from a query string (read.html?work=…&c=…). Both are cached by their
   address, which is what the reader's history and links carry. */

self.addEventListener('install', function (ev) {
  ev.waitUntil(
    caches.open(SHELL).then(function (c) {
      /* One failed file must not fail the whole install. */
      return Promise.all(PRECACHE.map(function (u) {
        return c.add(new Request(u, { cache: 'reload' })).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (ev) {
  ev.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k.indexOf(VERSION) !== 0) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

function isAsset(url) {
  return url.pathname.indexOf('/assets/') !== -1;
}

/* The cache is keyed by the whole address, query string included, which is
   what makes read.html?work=jps-genesis&c=1 and …&c=2 two entries. */

self.addEventListener('fetch', function (ev) {
  var req = ev.request;
  if (req.method !== 'GET') return;

  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  /* Assets: serve from cache at once, and quietly refresh behind it. */
  if (isAsset(url)) {
    ev.respondWith(
      caches.match(req).then(function (hit) {
        var live = fetch(req).then(function (res) {
          if (res && res.ok) {
            caches.open(SHELL).then(function (c) { c.put(req, res.clone()); });
          }
          return res;
        }).catch(function () { return hit; });
        return hit || live;
      })
    );
    return;
  }

  /* Pages: the network first, because the library grows. What comes back is
     kept, so the same chapter opens on a train. */
  ev.respondWith(
    fetch(req).then(function (res) {
      if (res && res.ok && res.type === 'basic') {
        var copy = res.clone();
        caches.open(PAGES).then(function (c) { c.put(req, copy); });
      }
      return res;
    }).catch(function () {
      return caches.match(req).then(function (hit) {
        return hit || caches.match('offline.html');
      });
    })
  );
});

/* A page can ask for a list of chapters to be kept — that is how a reading
   plan is saved for a week away from the network. */
self.addEventListener('message', function (ev) {
  var msg = ev.data || {};
  if (msg.type !== 'keep' || !Array.isArray(msg.urls)) return;
  var port = ev.ports && ev.ports[0];
  caches.open(PAGES).then(function (c) {
    var done = 0;
    return Promise.all(msg.urls.map(function (u) {
      return c.match(u).then(function (hit) {
        if (hit) { done++; return; }
        return fetch(u, { credentials: 'same-origin' }).then(function (res) {
          if (res && res.ok) { done++; return c.put(u, res); }
        }).catch(function () {});
      });
    })).then(function () {
      if (port) port.postMessage({ kept: done, of: msg.urls.length });
    });
  });
});
