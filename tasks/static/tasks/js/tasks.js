(function () {
  'use strict';

  function setVoteBtnState(btn, isActive) {
    btn.classList.toggle('active-vote', isActive);
    var icon = btn.querySelector('i');
    if (icon) {
      icon.className = 'fas ' + (isActive ? btn.dataset.iconActive : btn.dataset.iconInactive);
    }
    var textNode = Array.from(btn.childNodes).find(function (n) {
      return n.nodeType === Node.TEXT_NODE && n.textContent.trim();
    });
    if (textNode) {
      textNode.textContent = ' ' + (isActive ? btn.dataset.textActive : btn.dataset.textInactive);
    }
    var newTitle = isActive ? btn.dataset.tooltipActive : btn.dataset.tooltipInactive;
    if (newTitle) {
      btn.setAttribute('title', newTitle);
      if (typeof bootstrap !== 'undefined') {
        var tip = bootstrap.Tooltip.getInstance(btn);
        if (tip) { tip.dispose(); new bootstrap.Tooltip(btn, { trigger: 'hover' }); }
      }
    }
  }

  function updateVoteCounts(form, data) {
    var card = form.closest('.proposal-card');
    if (card) {
      var sigSpan = card.querySelector('.proposal-signatures');
      if (sigSpan) {
        var icon = sigSpan.querySelector('i');
        if (icon) icon = icon.cloneNode(true);
        sigSpan.textContent = '';
        if (icon) sigSpan.appendChild(icon);
        sigSpan.appendChild(document.createTextNode(' ' + data.votes_up));
      }
    }
    var badge = document.querySelector('[data-votes-badge]');
    if (badge) {
      badge.textContent = badge.dataset.votesBadge + data.votes_score;
    }
  }

  function handleVoteClick(e) {
    var btn = e.target.closest('.task-vote-btn');
    if (!btn) return;
    var form = btn.closest('form');
    if (!form) return;

    // Prevent form submission and stop click reaching card-body onclick / card-header toggleCard
    e.preventDefault();
    e.stopPropagation();

    var value = parseInt(form.querySelector('input[name="value"]').value, 10);
    var csrf = form.querySelector('[name="csrfmiddlewaretoken"]').value;

    fetch(form.action, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({ value: value, csrfmiddlewaretoken: csrf }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var row = form.closest('.task-vote-row, .task-actions');
        if (!row) return;
        var upBtn = row.querySelector('.task-vote-btn.up');
        var downBtn = row.querySelector('.task-vote-btn.down');
        if (upBtn) setVoteBtnState(upBtn, data.vote === 1);
        if (downBtn) setVoteBtnState(downBtn, data.vote === -1);
        updateVoteCounts(form, data);
      })
      .catch(function () {
        // silent fail — card stays open, user can retry
      });
  }

  // Capture phase: fires before card-body onclick and card-header toggleCard
  document.addEventListener('click', handleVoteClick, true);

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
      new bootstrap.Tooltip(el, { trigger: 'hover' });
    });
  });
}());
