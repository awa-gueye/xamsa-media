/* Service worker de Xamsa Media (PWA installable + hors-ligne). Servi sur /sw.js. */
var CACHE = 'xamsa-v34';
var ESSENTIELS = [
  '/hors-ligne/',
  '/static/img/logo.png',
  '/static/img/icon-192.png',
  '/static/img/icon-512.png'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(ESSENTIELS); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) { if (k !== CACHE) return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;                    // pas les POST (chatbot, formulaires)
  var url = new URL(req.url);
  if (url.origin !== location.origin) return;          // pas les ressources externes (images RSS...)
  if (url.pathname.indexOf('/admin') === 0) return;    // jamais mettre l'admin en cache

  // Fichiers statiques : cache d'abord (ils sont versionnes par ?v=, donc surs a garder).
  if (url.pathname.indexOf('/static/') === 0) {
    e.respondWith(
      caches.match(req).then(function (hit) {
        return hit || fetch(req).then(function (res) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
          return res;
        });
      })
    );
    return;
  }

  // Pages : reseau d'abord (contenu frais), sinon cache, sinon page hors-ligne.
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); });
        return res;
      }).catch(function () {
        return caches.match(req).then(function (hit) { return hit || caches.match('/hors-ligne/'); });
      })
    );
  }
});
