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
})();
