(function () {
  'use strict';

  var CSRF = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';

  // options: { reorderUrl, handle (CSS selector), onSaved, onError, msg: { reorder_error, network_error } }
  window.initSortableList = function (listEl, options) {
    if (!listEl || typeof Sortable === 'undefined') return;

    var opts = options || {};

    return Sortable.create(listEl, {
      handle: opts.handle || undefined,
      animation: 150,
      ghostClass: 'sortable-ghost',
      chosenClass: 'sortable-chosen',
      onEnd: function () {
        var items = Array.from(listEl.children).map(function (li, idx) {
          return { id: parseInt(li.dataset.id, 10), order: idx };
        });
        fetch(opts.reorderUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF,
          },
          body: JSON.stringify(items),
        })
          .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
          .then(function (res) {
            if (!res.ok) {
              if (opts.onError) opts.onError(res.data.error || (opts.msg && opts.msg.reorder_error) || 'Reorder failed.');
            } else {
              if (opts.onSaved) opts.onSaved();
            }
          })
          .catch(function () {
            if (opts.onError) opts.onError((opts.msg && opts.msg.network_error) || 'Network error.');
          });
      },
    });
  };
}());
