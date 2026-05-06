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
      var countEl = card.querySelector('.proposal-signatures-count');
      if (countEl) {
        countEl.textContent = data.votes_up;
      }
      // Vote changed — popover content may be stale, drop cached html for this task
      var helpersBtn = card.querySelector('[data-task-helpers]');
      if (helpersBtn) {
        helpersCache.delete(helpersBtn.dataset.taskHelpers);
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
    initHelpersPopovers();
  });

  // ─── Helpers popover ──────────────────────────────────────────
  var helpersCache = new Map();
  var i18n = (window.TASK_HELPERS_I18N || {});
  var supportsHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  function sanitize(html) {
    if (typeof DOMPurify !== 'undefined') {
      return DOMPurify.sanitize(html, { ADD_ATTR: ['target'] });
    }
    return html;
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function renderHelpersHtml(data) {
    if (!data.total) {
      return '<div class="helpers-popover-empty">' + escapeHtml(i18n.empty || 'No one helps yet') + '</div>';
    }
    var items = data.helpers.map(function (h) {
      var avatar = h.avatar_url
        ? '<img src="' + escapeHtml(h.avatar_url) + '" alt="">'
        : escapeHtml(h.username.slice(0, 2).toUpperCase());
      return '<a class="helpers-popover-item" href="' + escapeHtml(h.profile_url) + '">'
        + '<span class="helpers-popover-avatar">' + avatar + '</span>'
        + '<span class="helpers-popover-name">' + escapeHtml(h.username) + '</span>'
        + '</a>';
    }).join('');
    var more = '';
    if (data.extra > 0) {
      var moreText = (i18n.more || 'and {n} more — see all').replace('{n}', data.extra);
      more = '<a class="helpers-popover-more" href="' + escapeHtml(data.task_url) + '">'
           + escapeHtml(moreText) + '</a>';
    }
    return '<div class="helpers-popover-list">' + items + more + '</div>';
  }

  function loadHelpers(btn, popover) {
    var taskId = btn.dataset.taskHelpers;
    if (helpersCache.has(taskId)) {
      popover.setContent({ '.popover-body': sanitize(helpersCache.get(taskId)) });
      return;
    }
    fetch(btn.dataset.helpersUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var html = renderHelpersHtml(data);
        helpersCache.set(taskId, html);
        popover.setContent({ '.popover-body': sanitize(html) });
      })
      .catch(function () {
        var err = '<div class="helpers-popover-empty">' + escapeHtml(i18n.error || 'Could not load helpers') + '</div>';
        popover.setContent({ '.popover-body': sanitize(err) });
      });
  }

  function initHelpersPopovers() {
    if (typeof bootstrap === 'undefined') return;
    var buttons = document.querySelectorAll('[data-task-helpers]');
    buttons.forEach(function (btn) {
      var popover = new bootstrap.Popover(btn, {
        sanitize: false,
        html: true,
        customClass: 'helpers-popover',
      });

      var hideTimer = null;
      var clearHide = function () { if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; } };
      var scheduleHide = function () {
        clearHide();
        hideTimer = setTimeout(function () { popover.hide(); }, 150);
      };

      btn.addEventListener('show.bs.popover', function () { loadHelpers(btn, popover); });

      if (supportsHover) {
        btn.addEventListener('mouseenter', function () { clearHide(); popover.show(); });
        btn.addEventListener('mouseleave', scheduleHide);
        btn.addEventListener('focus', function () { popover.show(); });
        btn.addEventListener('blur', scheduleHide);
        btn.addEventListener('shown.bs.popover', function () {
          var tip = document.getElementById(btn.getAttribute('aria-describedby'));
          if (!tip) return;
          tip.addEventListener('mouseenter', clearHide);
          tip.addEventListener('mouseleave', scheduleHide);
        });
      } else {
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          var tipId = btn.getAttribute('aria-describedby');
          if (tipId && document.getElementById(tipId)) {
            popover.hide();
          } else {
            popover.show();
          }
        });
        document.addEventListener('click', function (e) {
          var tipId = btn.getAttribute('aria-describedby');
          if (!tipId) return;
          var tip = document.getElementById(tipId);
          if (tip && !tip.contains(e.target) && !btn.contains(e.target)) {
            popover.hide();
          }
        });
      }
    });
  }
}());
