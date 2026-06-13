/**
 * @jest-environment jsdom
 *
 * Testy onRoomAdded — live wstawienie kafelka pokoju prywatnego w sidebarze po
 * 1. wiadomosci (puste prywatne pokoje sa ukryte, patrz commit 9c8bda8).
 * Serwer wysyla room_added {room_id, html} z gotowym room_link.html; klient
 * wstawia go do #cat-private. Idempotencja: nie duplikuje istniejacego kafelka.
 *
 * DLACZEGO kopia 1:1 zamiast importu: jest.config.js ma `transform: {}` (brak
 * Babel/ts-jest), a chat.js to ES module. `import` rzuca "Cannot use import
 * statement outside a module". Caly katalog testow trzyma sie wzorca kopiowania —
 * patrz sidebar_update.test.js / own_identity.test.js. Sync recznie przy zmianie.
 */

// ── wierna kopia z chat.js (synchronizowac przy zmianie!) ──────────────────
function getRoomLinkDiv(room_id) {
    return document.querySelector(`.room-link[data-room-id="${room_id}"]`);
}

function onRoomAdded(payload) {
    const { room_id, html } = payload || {};
    if (!room_id || !html) return;
    // Idempotencja: kafelek juz jest (np. druga karta / wyscig) — nic nie rob.
    if (getRoomLinkDiv(room_id)) return;
    const container = document.getElementById('cat-private');
    if (!container) return;
    container.insertAdjacentHTML('afterbegin', html);

    // Dropdown chevrona dopinany recznie (delegacja nie obejmuje bootstrap init).
    // W jsdom brak `bootstrap` globala — guard czyni to no-opem (testujemy mutacje DOM).
    const chevron = container.querySelector(`.room-link[data-room-id="${room_id}"] .room-link__chevron[data-bs-toggle="dropdown"]`);
    if (chevron && typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
        new bootstrap.Dropdown(chevron, {
            popperConfig(defaultConfig) {
                return { ...defaultConfig, strategy: 'fixed' };
            },
        });
    }
}

// ── helpers ────────────────────────────────────────────────────────────────
function tileHtml(roomId, name = 'Alice') {
    return `<div class="room-link" data-room-type="private" data-room-id="${roomId}">
        <span class="room-name">${name}</span></div>`;
}

// ── testy ──────────────────────────────────────────────────────────────────
describe('onRoomAdded', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div class="nav-cat-content open" id="cat-private">
                <div class="room-link" data-room-id="1"><span class="room-name">Bob</span></div>
            </div>`;
    });

    test('wstawia nowy kafelek na gore #cat-private', () => {
        onRoomAdded({ room_id: 5, html: tileHtml(5, 'Alice') });
        const container = document.getElementById('cat-private');
        expect(container.firstElementChild.dataset.roomId).toBe('5');
        expect(getRoomLinkDiv(5)).not.toBeNull();
    });

    test('idempotencja: nie duplikuje gdy kafelek juz istnieje', () => {
        onRoomAdded({ room_id: 1, html: tileHtml(1, 'Bob-zdublowany') });
        const tiles = document.querySelectorAll('.room-link[data-room-id="1"]');
        expect(tiles.length).toBe(1);
        // istniejacy nietkniety
        expect(tiles[0].querySelector('.room-name').textContent).toBe('Bob');
    });

    test('brak room_id lub html: bezpieczny no-op', () => {
        const before = document.getElementById('cat-private').children.length;
        onRoomAdded({ room_id: 5 });
        onRoomAdded({ html: tileHtml(5) });
        onRoomAdded(null);
        expect(document.getElementById('cat-private').children.length).toBe(before);
    });

    test('brak #cat-private w DOM: nie rzuca', () => {
        document.body.innerHTML = '<div>no private section</div>';
        expect(() => onRoomAdded({ room_id: 9, html: tileHtml(9) })).not.toThrow();
    });
});
