/* AJAX up/down voting on głosowania arguments.
 *
 * Posts a single click to the per-argument vote endpoint and updates the
 * counts + support bar in place, mirroring the chat reaction UX. The bar
 * thresholds (60 / 40 / min 3) are the canonical spec from zzz/reactions.py
 * — keep them in sync with that module (and chat's templates.js).
 */
(function () {
  'use strict';

  function getCsrf() {
    var grid = document.querySelector('.args-grid');
    return grid ? grid.dataset.csrf : '';
  }

  function barClass(pct) {
    if (pct >= 60) return 'vote-bar--positive';
    if (pct >= 40) return 'vote-bar--neutral';
    return 'vote-bar--negative';
  }

  function applyVote(box, data) {
    var up = box.querySelector('.arg-vote-count[data-count="up"]');
    var down = box.querySelector('.arg-vote-count[data-count="down"]');
    if (up) up.textContent = data.upvotes;
    if (down) down.textContent = data.downvotes;

    // One vote per user: only the just-cast button stays active.
    box.querySelectorAll('.arg-vote-btn').forEach(function (b) {
      b.classList.toggle('active', data.active && b.dataset.event === data.event);
    });

    var total = data.upvotes + data.downvotes;
    var pct = total ? Math.round((data.upvotes / total) * 100) : 0;
    var show = total >= 3;

    var bar = box.querySelector('.arg-vote-bar');
    var fill = bar ? bar.querySelector('.vote-bar-fill') : null;
    var label = box.querySelector('.arg-vote-label');
    if (bar) bar.hidden = !show;
    if (fill) {
      fill.style.width = pct + '%';
      fill.className = 'vote-bar-fill ' + barClass(pct);
    }
    if (label) {
      label.hidden = !show;
      label.textContent = pct + '% ' + (label.dataset.word || '');
    }
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.arg-vote-btn');
    if (!btn) return;
    var box = btn.closest('.arg-votes');
    if (!box || !box.dataset.voteUrl) return;

    btn.disabled = true;
    fetch(box.dataset.voteUrl, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrf(),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: new URLSearchParams({ event: btn.dataset.event }),
    })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) { applyVote(box, data); })
      .catch(function () { /* keep current UI on failure */ })
      .finally(function () { btn.disabled = false; });
  });
})();
