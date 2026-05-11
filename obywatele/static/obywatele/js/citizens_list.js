document.addEventListener('DOMContentLoaded', function () {
    const STORAGE_KEY = 'obywatele-view';
    const listView = document.getElementById('citizens-list-view');
    const gridView = document.getElementById('citizens-grid-view');
    const btnList = document.getElementById('btn-view-list');
    const btnGrid = document.getElementById('btn-view-grid');
    const countEl = document.getElementById('citizens-count');
    const searchInput = document.getElementById('citizens-search');

    // ── View toggle (grid / list) ──
    function setView(mode) {
        const isGrid = mode === 'grid';
        listView.classList.toggle('d-none', isGrid);
        gridView.classList.toggle('d-none', !isGrid);
        btnList.classList.toggle('active', !isGrid);
        btnGrid.classList.toggle('active', isGrid);
        localStorage.setItem(STORAGE_KEY, mode);
    }

    const saved = localStorage.getItem(STORAGE_KEY);
    setView(saved || (window.innerWidth < 768 ? 'grid' : 'list'));

    btnList.addEventListener('click', () => setView('list'));
    btnGrid.addEventListener('click', () => setView('grid'));

    // ── Live search ──
    let searchTimer;
    searchInput.addEventListener('input', function () {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            const q = this.value.trim().toLowerCase();
            const rows = listView.querySelectorAll('.user-row');
            const cards = gridView.querySelectorAll('.citizen-card');
            let visible = 0;

            rows.forEach(row => {
                const match = !q || row.dataset.search.toLowerCase().includes(q);
                row.classList.toggle('d-none', !match);
                if (match) visible++;
            });
            cards.forEach(card => {
                const match = !q || card.dataset.search.toLowerCase().includes(q);
                card.classList.toggle('d-none', !match);
            });

            if (countEl) countEl.textContent = q ? visible : rows.length;
        }, 150);
    });

    // ── Row click → detail ──
    listView.querySelectorAll('.user-row').forEach(row => {
        row.addEventListener('click', function (e) {
            if (!e.target.closest('button, a')) {
                window.location.href = `/obywatele/poczekalnia/${this.dataset.userId}/`;
            }
        });
    });

    // ── Card click → detail ──
    gridView.querySelectorAll('.citizen-card').forEach(card => {
        card.addEventListener('click', function () {
            window.location.href = `/obywatele/poczekalnia/${this.dataset.userId}/`;
        });
    });

    // ── Copy email ──
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', function (e) {
            e.stopPropagation();
            navigator.clipboard.writeText(this.dataset.email).then(() => {
                const orig = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i>';
                this.classList.remove('btn-light');
                this.classList.add('btn-success');
                setTimeout(() => {
                    this.innerHTML = orig;
                    this.classList.remove('btn-success');
                    this.classList.add('btn-light');
                }, 1500);
            });
        });
    });
});
