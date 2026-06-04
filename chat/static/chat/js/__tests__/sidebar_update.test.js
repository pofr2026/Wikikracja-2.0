/**
 * @jest-environment jsdom
 *
 * Testy updateSidebarForMessage — aktualizacja podgladu pokoju w sidebarze.
 * Pokrywa regresje #4: edycja ostatniej wiadomosci nie odswiezala preview.
 *
 * Testowane zachowania:
 *   - reorder=true (default): aktualizuje pola + przesuwa pokoj na gore listy
 *   - reorder=false: aktualizuje pola, NIE przesuwa (uzywane przy edycji — nie jest to nowa aktywnosc)
 *
 * Kontrakt z domapi.js (synchronizowac przy zmianie — funkcja kopiowana 1:1).
 */

// ── stub i18n ──────────────────────────────────────────────────────────────
const _ = (key) => key;

function _relativeChatDate(ts) { return 'today'; }

// ── wierna kopia z domapi.js (synchronizowac przy zmianie!) ───────────────
function updateSidebarForMessage(msg, {reorder = true, bumpActivity = reorder} = {}) {
    const roomLink = document.querySelector(`.room-link[data-room-id="${msg.room_id}"]`);
    if (!roomLink) return;

    if (bumpActivity) {
        roomLink.dataset.lastActivity = Math.floor(msg.timestamp / 1000);
        const dateEl = roomLink.querySelector('.room-link__date');
        if (dateEl) dateEl.textContent = _relativeChatDate(msg.timestamp);
    }

    const senderEl = roomLink.querySelector('.room-link__sender');
    if (senderEl) senderEl.textContent = (msg.anonymous ? _('Anonymous') : (msg.username || '—')) + ':';

    const snippetEl = roomLink.querySelector('.room-link__snippet');
    if (snippetEl) {
        const tmp = document.createElement('div');
        tmp.innerHTML = msg.message || '';
        const text = tmp.textContent.replace(/\s+/g, ' ').trim();
        snippetEl.textContent = text || _('attachment');
    }

    if (reorder) {
        const container = roomLink.closest('.nav-cat-content, #room-list-flat');
        if (container && container.firstElementChild !== roomLink) {
            container.prepend(roomLink);
        }
    }
}

// ── helpers ────────────────────────────────────────────────────────────────
function makeRoomLink(roomId, snippetText = 'old text') {
    const div = document.createElement('div');
    div.className = 'room-link';
    div.dataset.roomId = String(roomId);
    div.innerHTML = `
        <span class="room-link__date">yesterday</span>
        <span class="room-link__sender">Alice:</span>
        <span class="room-link__snippet">${snippetText}</span>
    `;
    return div;
}

function makeMsg(roomId, text = 'new text') {
    return { room_id: roomId, username: 'Bob', anonymous: false, message: text, timestamp: Date.now() };
}

// ── testy ──────────────────────────────────────────────────────────────────
describe('updateSidebarForMessage', () => {
    let container;

    beforeEach(() => {
        document.body.innerHTML = '<div id="room-list-flat"></div>';
        container = document.getElementById('room-list-flat');
    });

    test('aktualizuje snippet i sender', () => {
        container.appendChild(makeRoomLink(1));
        updateSidebarForMessage(makeMsg(1, 'zaktualizowana tresc'));
        expect(container.querySelector('.room-link__snippet').textContent).toBe('zaktualizowana tresc');
        expect(container.querySelector('.room-link__sender').textContent).toBe('Bob:');
    });

    test('reorder=true (default): przesuwa pokoj na gore listy', () => {
        const first = makeRoomLink(1, 'room 1');
        const second = makeRoomLink(2, 'room 2');
        container.appendChild(first);
        container.appendChild(second);

        // Drugi pokoj dostaje nowa wiadomosc → powinien wskoczyc na gore
        updateSidebarForMessage(makeMsg(2));

        expect(container.firstElementChild.dataset.roomId).toBe('2');
    });

    test('reorder=false: aktualizuje snippet ale NIE przesuwa pokoju', () => {
        const first = makeRoomLink(1, 'room 1');
        const second = makeRoomLink(2, 'room 2');
        container.appendChild(first);
        container.appendChild(second);

        // Edycja ostatniej wiadomosci w drugim pokoju — nie jest to nowa aktywnosc
        updateSidebarForMessage(makeMsg(2, 'edytowana tresc'), {reorder: false});

        // Kolejnosc bez zmian — room 1 nadal pierwszy
        expect(container.firstElementChild.dataset.roomId).toBe('1');
        // Ale snippet zaktualizowany
        expect(container.children[1].querySelector('.room-link__snippet').textContent).toBe('edytowana tresc');
    });

    test('reorder=false nie aktualizuje daty ani dataset.lastActivity', () => {
        const link = makeRoomLink(1);
        link.dataset.lastActivity = '1000';
        link.querySelector('.room-link__date').textContent = 'yesterday';
        container.appendChild(link);

        const msg = makeMsg(1, 'nowy tekst');
        msg.timestamp = Date.now() + 999999;   // wyraznie pozniejszy niz 1000
        updateSidebarForMessage(msg, {reorder: false});

        // dataset.lastActivity i data NIE powinny sie zmienic
        expect(link.dataset.lastActivity).toBe('1000');
        expect(link.querySelector('.room-link__date').textContent).toBe('yesterday');
        // snippet nadal zaktualizowany
        expect(link.querySelector('.room-link__snippet').textContent).toBe('nowy tekst');
    });

    test('brak rooma w DOM: nie rzuca', () => {
        expect(() => updateSidebarForMessage(makeMsg(999))).not.toThrow();
    });
});
