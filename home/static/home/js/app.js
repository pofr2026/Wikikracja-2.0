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
    // Tab persistence for task list - from task_list.html
    // ============================================================
    // Tab persistence: Check localStorage for last active tab
    const lastTab = localStorage.getItem('tasks_tab');
    if (lastTab) {
        const tabTrigger = document.querySelector(`[data-bs-target="#${lastTab}"]`);
        if (tabTrigger) {
            const tab = new bootstrap.Tab(tabTrigger);
            tab.show();
        }
    }

    // Save tab selection on tab change
    document.querySelectorAll('button[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            const targetId = event.target.getAttribute('data-bs-target').substring(1);
            localStorage.setItem('tasks_tab', targetId);
        });
    });

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
// Theme toggle — handler is in base.html; applyTheme exposed globally for other scripts
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
    window.toggleCard = function(pk, storage_key) {
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

    /* ── przełącznik widoku ── */
    window.setView = function(mode, storage_key) {
        const list = document.getElementById('proposals-list');
        const btnList = document.getElementById('btn-list');
        const btnGrid = document.getElementById('btn-grid');
        if (!list) return;

        if (mode === 'grid') {
            list.classList.add('view-grid');
            btnGrid.classList.add('active');
            btnList.classList.remove('active');
        } else {
            list.classList.remove('view-grid');
            btnList.classList.add('active');
            btnGrid.classList.remove('active');
        }
        localStorage.setItem(storage_key, mode);
    };
});

document.addEventListener('DOMContentLoaded', function() {
    const TASK_STORAGE_KEY = 'tasks_view';
    window.setTaskView = function(pk) {
        window.setView(pk, TASK_STORAGE_KEY)
    }
    const PROPOSALS_STORAGE_KEY = 'proposals_view';
    window.setProposalsView = function(pk) {
        window.setView(pk, PROPOSALS_STORAGE_KEY)
    }
    const ELIBRARY_STORAGE_KEY = 'elibrary_view';
    window.setElibraryView = function(pk) {
        window.setView(pk, ELIBRARY_STORAGE_KEY)
    }
    const BOARD_STORAGE_KEY = 'board_view';
    window.setBoardView = function(pk) {
        window.setView(pk, BOARD_STORAGE_KEY)
    }

    setTaskView(localStorage.getItem(TASK_STORAGE_KEY) || 'list');
    setProposalsView(localStorage.getItem(PROPOSALS_STORAGE_KEY) || 'list');
    setElibraryView(localStorage.getItem(ELIBRARY_STORAGE_KEY) || 'list');
    setBoardView(localStorage.getItem(BOARD_STORAGE_KEY) || 'list');
});

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