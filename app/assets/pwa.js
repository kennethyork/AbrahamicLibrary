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
