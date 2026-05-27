/**
 * Main application JavaScript
 * Consolidates inline scripts from various templates
 */

// ============================================================
// Global notification permission banner handler - from base.html
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    const banner = document.getElementById('notification-permission-banner');
    const blockedBanner = document.getElementById('notification-blocked-banner');
    if (!banner || !blockedBanner) return;

    // Check if Notification API is supported
    if (!('Notification' in window)) {
        console.log('Notifications not supported');
        return;
    }

    //console.log('Notification permission status:', Notification.permission);

    // Check if user has already dismissed the banner
    const dismissed = localStorage.getItem('notification-banner-dismissed');
    const blockedDismissed = localStorage.getItem('notification-blocked-dismissed');

    // Show appropriate banner based on permission state
    if (Notification.permission === 'default' && !dismissed) {
        banner.style.display = 'block';
    } else if (Notification.permission === 'denied' && !blockedDismissed) {
        blockedBanner.style.display = 'block';
    }

    // Handle "Enable Notifications" button
    document.getElementById('enable-notifications-global')?.addEventListener('click', async function(e) {
        e.preventDefault();
        console.log('Enable notifications clicked, current permission:', Notification.permission);

        try {
            // Request permission
            const permission = await Notification.requestPermission();
            console.log('Permission result:', permission);

            if (permission === 'granted') {
                banner.style.display = 'none';
                localStorage.removeItem('notification-banner-dismissed');
                // Reload to initialize push notifications
                location.reload();
            } else if (permission === 'denied') {
                // Show blocked banner
                banner.style.display = 'none';
                blockedBanner.style.display = 'block';
                // Remember that user denied
                localStorage.setItem('notification-blocked-dismissed', Date.now() + (30 * 24 * 60 * 60 * 1000));
            } else {
                // Permission is still 'default' - user dismissed the prompt
                console.log('User dismissed the permission prompt');
            }
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            // Show blocked banner on error
            banner.style.display = 'none';
            blockedBanner.style.display = 'block';
        }
    });

    // Handle "Not now" button
    document.getElementById('dismiss-notifications-banner')?.addEventListener('click', function() {
        banner.style.display = 'none';
        // Remember dismissal for 7 days
        const dismissedUntil = Date.now() + (7 * 24 * 60 * 60 * 1000);
        localStorage.setItem('notification-banner-dismissed', dismissedUntil);
    });

    // Handle "Dismiss" button on blocked banner
    document.getElementById('dismiss-blocked-banner')?.addEventListener('click', function() {
        blockedBanner.style.display = 'none';
        // Remember dismissal for 30 days
        const dismissedUntil = Date.now() + (30 * 24 * 60 * 60 * 1000);
        localStorage.setItem('notification-blocked-dismissed', dismissedUntil);
    });

    // Check if dismissal has expired
    if (dismissed && parseInt(dismissed) < Date.now()) {
        localStorage.removeItem('notification-banner-dismissed');
        if (Notification.permission === 'default') {
            banner.style.display = 'block';
        }
    }

    if (blockedDismissed && parseInt(blockedDismissed) < Date.now()) {
        localStorage.removeItem('notification-blocked-dismissed');
        if (Notification.permission === 'denied') {
            blockedBanner.style.display = 'block';
        }
    }

    // ============================================================
    // Year selector for bookkeeping report - from report_list.html
    // ============================================================
    const yearSelect = document.getElementById('yearSelect');
    if (yearSelect) {
        const reportListUrl = yearSelect.dataset.reportListUrl;
        yearSelect.addEventListener('change', function() {
            const selectedYear = this.value;
            window.location.href = reportListUrl + '?year=' + selectedYear;
        });
    }

    // ============================================================
    // Event form frequency toggle - from event_form.html
    // ============================================================
    const frequencyField = document.getElementById('id_frequency');
    const ordinalFieldsRow = document.getElementById('ordinal-fields-row');

    if (frequencyField && ordinalFieldsRow) {
        function toggleOrdinalFields() {
            if (frequencyField.value === 'monthly_ordinal') {
                ordinalFieldsRow.style.display = 'flex';
            } else {
                ordinalFieldsRow.style.display = 'none';
            }
        }

        // Initial state
        toggleOrdinalFields();

        // Listen for changes
        frequencyField.addEventListener('change', toggleOrdinalFields);
    }
});

// ============================================================
// Theme toggle — applyTheme exposed globally for other scripts
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    window.applyTheme = function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('app-theme', theme);
    }

    const btn = document.getElementById('theme-toggle-btn');
    if (btn) {
        btn.addEventListener('click', function() {
            applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    /* ── toggle pojedynczego kafelka ── */
    window.toggleCard = function(pk) {
        const card = document.getElementById('card-' + pk);
        const body = document.getElementById('body-' + pk);
        if (!card || !body) return;
        const isOpen = card.classList.contains('open');
        if (isOpen) {
            card.classList.remove('open');
            body.style.display = 'none';
        } else {
            card.classList.add('open');
            body.style.display = 'flex';
        }
    };
});

// ============================================================
// PagePrefs — globalny system zapamiętywania ustawień strony
// ------------------------------------------------------------
// Per-scope JSON w localStorage: { view, filters, tab }
//   - scope ustawia szablon przez `data-prefs-scope` na <html>
//   - filtry (URL params) restore'owane są w head-script (anti-FOUC)
//   - widok lista/grid: data-view="list|grid" + [data-view-container]
//   - tab persistence: Bootstrap tabs auto-wired
// ============================================================
(function() {
    'use strict';

    var KEY_PREFIX = 'wikikracja:prefs:';

    function scope() {
        return document.documentElement.dataset.prefsScope || '';
    }

    function read() {
        var s = scope();
        if (!s) return {};
        try { return JSON.parse(localStorage.getItem(KEY_PREFIX + s) || '{}'); }
        catch (e) { return {}; }
    }

    function write(patch) {
        var s = scope();
        if (!s) return;
        var data = Object.assign(read(), patch);
        localStorage.setItem(KEY_PREFIX + s, JSON.stringify(data));
    }

    function clear() {
        var s = scope();
        if (s) localStorage.removeItem(KEY_PREFIX + s);
    }

    function applyView(mode) {
        var container = document.querySelector('[data-view-container]');
        if (!container) return;
        container.classList.toggle('view-grid', mode === 'grid');
        document.querySelectorAll('[data-view]').forEach(function(btn) {
            btn.classList.toggle('active', btn.dataset.view === mode);
        });
    }

    function setView(mode) {
        applyView(mode);
        write({ view: mode });
    }

    function saveCurrentFilters() {
        if (scope()) write({ filters: window.location.search });
    }

    // One-shot migracja starych kluczy → nowy format JSON per scope
    function migrateLegacyKeys() {
        var migrations = {
            'tasks':      [{ k: 'tasks_view',     p: 'view' }, { k: 'tasks_tab', p: 'tab' }],
            'glosowania': [{ k: 'proposals_view', p: 'view' }],
            'board':      [{ k: 'board_view',     p: 'view' }],
            'activity':   [{ k: 'activity_view',  p: 'view' }]
        };
        Object.keys(migrations).forEach(function(scopeName) {
            var newKey = KEY_PREFIX + scopeName;
            if (localStorage.getItem(newKey) !== null) return; // już zmigrowano
            var data = {};
            var found = false;
            migrations[scopeName].forEach(function(m) {
                var v = localStorage.getItem(m.k);
                if (v !== null) { data[m.p] = v; found = true; }
            });
            if (found) {
                localStorage.setItem(newKey, JSON.stringify(data));
                migrations[scopeName].forEach(function(m) { localStorage.removeItem(m.k); });
            }
        });
    }

    function init() {
        if (!scope()) return;

        // 1. Widok lista/grid (filtry URL już zrestore'owane przez head-script)
        applyView(read().view || 'list');

        // 2. Zapisz aktualny URL (gdy ma params — pokrywa reload, klik linka sortowania)
        if (window.location.search) saveCurrentFilters();

        // 3. Patch history.pushState — łapie zmiany URL przez JS (kategoria filter w tasks/board)
        var origPush = history.pushState;
        history.pushState = function() {
            var ret = origPush.apply(this, arguments);
            saveCurrentFilters();
            return ret;
        };
        window.addEventListener('popstate', saveCurrentFilters);

        // 4. Auto-wire view toggle buttons
        document.querySelectorAll('[data-view]').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                setView(btn.dataset.view);
            });
        });

        // 5. Tab persistence (Bootstrap tabs) w tym samym JSON
        var savedTab = read().tab;
        if (savedTab && typeof bootstrap !== 'undefined') {
            var trigger = document.querySelector('[data-bs-target="#' + savedTab + '"]');
            if (trigger) new bootstrap.Tab(trigger).show();
        }
        document.querySelectorAll('button[data-bs-toggle="tab"]').forEach(function(tab) {
            tab.addEventListener('shown.bs.tab', function(e) {
                var targetId = e.target.getAttribute('data-bs-target').substring(1);
                write({ tab: targetId });
            });
        });
    }

    migrateLegacyKeys();

    window.PagePrefs = {
        init: init,
        setView: setView,
        read: read,
        write: write,
        clear: clear,
        saveCurrentFilters: saveCurrentFilters
    };

    document.addEventListener('DOMContentLoaded', init);
})();

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('topbar-search-form');
    const btn = document.getElementById('topbar-filter-btn');
    const panel = document.getElementById('topbar-filter-panel');
    const allBtn = document.getElementById('topbar-select-all');
    const qInput = document.getElementById('topbar-q');
    const cbs = document.querySelectorAll('.tb-cb');
    if (!form || !btn) return;

    const urlCats = new URLSearchParams(window.location.search).getAll('cat');

    function setChip(cb, on) {
        cb.checked = on;
        const chip = cb.closest('.tb-chip');
        if (on) chip.classList.add('on'); else chip.classList.remove('on');
    }
    function syncBtn() {
        const n = document.querySelectorAll('.tb-cb:checked').length;
        const partial = n < cbs.length;
        btn.style.color = partial ? 'var(--accent)' : 'var(--text-muted)';
        btn.style.borderColor = partial ? 'var(--accent)' : 'var(--border)';
    }

    cbs.forEach(function(cb) {
        setChip(cb, urlCats.length === 0 || urlCats.indexOf(cb.value) !== -1);
    });
    syncBtn();

    btn.addEventListener('click', function(e) {
        e.stopPropagation();
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    });
    document.addEventListener('click', function(e) {
        if (!panel.contains(e.target) && e.target !== btn)
            panel.style.display = 'none';
    });
    cbs.forEach(function(cb) {
        cb.addEventListener('change', function() {
            setChip(cb, cb.checked);
            syncBtn();
            if (qInput && qInput.value.trim())
                setTimeout(function() { form.submit(); }, 80);
        });
    });
    allBtn.addEventListener('click', function() {
        cbs.forEach(function(cb) { setChip(cb, true); });
        syncBtn();
        if (qInput && qInput.value.trim()) form.submit();
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Board category filter
    const categoryChips = document.querySelectorAll('.category-chip');
    categoryChips.forEach(function(chip) {
        chip.addEventListener('click', function() {
            const category = this.dataset.category;
            const url = new URL(window.location);
            const currentCategory = url.searchParams.get('category');

            if (currentCategory === category) {
                // Toggle off - remove category parameter
                url.searchParams.delete('category');
            } else {
                // Set new category
                url.searchParams.set('category', category);
            }

            window.location.href = url.toString();
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    (function() {
        const toggle = document.getElementById('sidebar-toggle');
        if (toggle) {
            toggle.addEventListener('click', function() {
                document.getElementById('sidebar').classList.toggle('sidebar-open');
                const overlay = document.getElementById('sidebar-overlay');
                overlay.style.display = overlay.style.display === 'none' ? 'block' : 'none';
            });
        }
    })();
});

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const mainArea = document.querySelector('.main-area');
    const btn = document.getElementById('sidebar-collapse-btn');
    const icon = document.getElementById('sidebar-collapse-icon');
    if (!sidebar || !btn) return;

    const STORAGE_KEY = 'sidebar_collapsed';

    function applyState(collapsed) {
        if (collapsed) {
            sidebar.classList.add('collapsed');
            mainArea.classList.add('sidebar-collapsed');
            icon.classList.replace('fa-angles-left', 'fa-angles-right');
        } else {
            sidebar.classList.remove('collapsed');
            mainArea.classList.remove('sidebar-collapsed');
            icon.classList.replace('fa-angles-right', 'fa-angles-left');
        }
    }
    applyState(localStorage.getItem(STORAGE_KEY) === 'true');

    // Toggle sidebar state on button click
    btn.addEventListener('click', function() {
        const isCollapsed = sidebar.classList.contains('collapsed');
        applyState(!isCollapsed);
        localStorage.setItem(STORAGE_KEY, String(!isCollapsed));
    });
});

// ============================================================
// Mark activity feed items as read - shared function
// ============================================================
window.initActivityFeedMarkRead = function(containerSelector, linkSelector) {
    var container = document.querySelector(containerSelector);
    if (!container) return;

    container.addEventListener('click', function(e) {
        var link = e.target.closest(linkSelector);
        if (!link) return;
        e.preventDefault();
        var contentType = link.getAttribute('data-content-type');
        var objectId = link.getAttribute('data-object-id');
        var url = link.getAttribute('href');
        if (!contentType || !objectId) {
            window.location.href = url;
            return;
        }
        fetch(window.MARK_AS_READ_URL || '/mark-as-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.CSRF_TOKEN || '',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
                content_type: contentType,
                object_id: objectId
            })
        }).finally(function() {
            window.location.href = url;
        });
    });
};

// Toggle .expandable blocks — clicking body toggles open/close (only when overflow detected).
function hasSelectedTextInside(container) {
    const selection = window.getSelection?.();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return false;
    if (!(selection.toString() || '').trim()) return false;
    const range = selection.getRangeAt(0);

    if (typeof range.intersectsNode === 'function') {
        try {
            return range.intersectsNode(container);
        } catch (err) {
            // Fall through to compatibility checks below.
        }
    }

    if (container.contains(range.startContainer) || container.contains(range.endContainer)) {
        return true;
    }

    const ancestor = range.commonAncestorContainer;
    const ancestorEl = ancestor.nodeType === Node.ELEMENT_NODE ? ancestor : ancestor.parentElement;
    return !!(ancestorEl && container.contains(ancestorEl));
}

document.addEventListener('click', function(e) {
    if (e.target.closest('a')) return;
    const body = e.target.closest('.expandable-body');
    const el = body?.closest('.expandable');
    if (!el?.classList.contains('has-overflow')) return;
    if (hasSelectedTextInside(body)) return;
    el.classList.toggle('is-open');
});

// Globalna inicjalizacja Bootstrap tooltipów — każdy [data-bs-toggle="tooltip"] działa
// bez per-page boilerplate'u. Trigger 'hover' (bez focus) żeby chip nie zostawał
// "kliknięty" po tap'ie na mobile.
document.addEventListener('DOMContentLoaded', function () {
    if (typeof bootstrap === 'undefined' || !bootstrap.Tooltip) return;
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        new bootstrap.Tooltip(el, { trigger: 'hover' });
    });
});