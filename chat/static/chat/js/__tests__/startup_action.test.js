/**
 * @jest-environment jsdom
 *
 * Testy decideStartupAction — czystej funkcji decydującej, co zrobić przy starcie chat.js,
 * na podstawie URL params (sidebar / dashboard badge) i obecności hash'a.
 *
 * Kontrakt z chat.js:
 *   - ?view=rooms       (sidebar)         — lista pokoi, filtr unread OFF, brak auto-joina,
 *                                            placeholder w obszarze wiadomosci
 *   - ?view=unread      (dashboard)       — lista pokoi, filtr unread ON, brak auto-joina.
 *                                            Empty state ("nie masz nieprzeczytanych" + ikona +
 *                                            instrukcja zdjac filtr) jest pochodna stanu filtra,
 *                                            obsluguje go applyUnreadFilter — nie ta funkcja.
 *   - hash #room_id=X   — zawsze bije URL params (uzytkownik wprost prosi o konkretny pokoj)
 *   - brak parametrow   — domyslne zachowanie (auto-join do ostatniego pokoju)
 */

// ── wierna kopia z chat.js (synchronizowac przy zmianie!) ────────────────────

function decideStartupAction({ search = '', hasHash = false, isMobile = false } = {}) {
    // Hash ma bezwzgledny priorytet — uzytkownik chce konkretny pokoj
    if (hasHash) {
        return { mode: 'default', joinAction: 'auto' };
    }

    const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);

    if (params.get('view') === 'rooms') {
        return {
            mode: 'rooms',
            unreadFilter: 'off',
            showPlaceholder: true,
            forceListVisible: true,
            mobileShowList: isMobile,
            joinAction: 'none',
            stripParam: 'view',
        };
    }

    // ?unread=1 to legacy alias (stare bookmark'y / push'e) — traktowany jak ?view=unread.
    const wantsUnreadView = params.get('view') === 'unread' || params.get('unread') === '1';
    if (wantsUnreadView) {
        return {
            mode: 'unread',
            unreadFilter: 'on',
            showPlaceholder: true,
            forceListVisible: true,
            mobileShowList: isMobile,
            joinAction: 'none',
            stripParam: params.get('unread') === '1' ? 'unread' : 'view',
        };
    }

    return { mode: 'default', joinAction: 'auto' };
}

// ── ?view=rooms (sidebar) ─────────────────────────────────────────────────────

describe('?view=rooms (sidebar)', () => {

    test('wylacza filtr unread, nie joinuje, wstawia placeholder, wymusza widocznosc listy', () => {
        const action = decideStartupAction({ search: '?view=rooms', isMobile: false });
        expect(action.mode).toBe('rooms');
        expect(action.unreadFilter).toBe('off');
        expect(action.joinAction).toBe('none');
        expect(action.showPlaceholder).toBe(true);
        expect(action.forceListVisible).toBe(true);
    });

    test('na mobile dodatkowo zadaje pokazania listy pokoi (room-list-showing)', () => {
        const action = decideStartupAction({ search: '?view=rooms', isMobile: true });
        expect(action.mobileShowList).toBe(true);
    });

    test('na desktop NIE ustawia mobileShowList', () => {
        const action = decideStartupAction({ search: '?view=rooms', isMobile: false });
        expect(action.mobileShowList).toBe(false);
    });

    test('strip param zeby URL nie sterczal po reload', () => {
        const action = decideStartupAction({ search: '?view=rooms' });
        expect(action.stripParam).toBe('view');
    });
});

// ── ?view=unread (dashboard, > 0 nieprzeczytanych) ────────────────────────────

describe('?view=unread (dashboard)', () => {

    test('wlacza filtr, nie joinuje, placeholder + lista widoczna', () => {
        const action = decideStartupAction({ search: '?view=unread' });
        expect(action.mode).toBe('unread');
        expect(action.unreadFilter).toBe('on');
        expect(action.joinAction).toBe('none');
        expect(action.showPlaceholder).toBe(true);
        expect(action.forceListVisible).toBe(true);
    });

    test('nie raportuje empty state — to robi applyUnreadFilter w runtime', () => {
        const action = decideStartupAction({ search: '?view=unread' });
        expect(action.showUnreadEmptyState).toBeUndefined();
    });

    test('mobile flag tez przeniesione', () => {
        const mobile = decideStartupAction({ search: '?view=unread', isMobile: true });
        const desktop = decideStartupAction({ search: '?view=unread', isMobile: false });
        expect(mobile.mobileShowList).toBe(true);
        expect(desktop.mobileShowList).toBe(false);
    });
});

// ── ?unread=1 — backwards-compat alias (stary URL z bookmark'ow / push'y) ────

describe('?unread=1 (legacy alias)', () => {

    test('traktowany identycznie jak ?view=unread', () => {
        const legacy = decideStartupAction({ search: '?unread=1', isMobile: false });
        const current = decideStartupAction({ search: '?view=unread', isMobile: false });
        // Wszystkie pola powinny byc identyczne OPROCZ stripParam (kasujemy ten,
        // ktory faktycznie byl w URL — zeby alias zniknal po reload).
        expect(legacy.mode).toBe(current.mode);
        expect(legacy.unreadFilter).toBe(current.unreadFilter);
        expect(legacy.joinAction).toBe(current.joinAction);
        expect(legacy.showPlaceholder).toBe(current.showPlaceholder);
        expect(legacy.forceListVisible).toBe(current.forceListVisible);
    });

    test('strip param wskazuje na "unread" (a nie "view")', () => {
        const action = decideStartupAction({ search: '?unread=1' });
        expect(action.stripParam).toBe('unread');
    });

    test('hash bije legacy alias tak samo jak ?view=unread', () => {
        const action = decideStartupAction({ search: '?unread=1', hasHash: true });
        expect(action.mode).toBe('default');
        expect(action.joinAction).toBe('auto');
    });
});

// ── Hash priority ─────────────────────────────────────────────────────────────

describe('hash #room_id=X bije URL params', () => {

    test('?view=rooms + hash → default (auto-join do pokoju z hasha)', () => {
        const action = decideStartupAction({ search: '?view=rooms', hasHash: true });
        expect(action.mode).toBe('default');
        expect(action.joinAction).toBe('auto');
    });

    test('?view=unread + hash → default', () => {
        const action = decideStartupAction({ search: '?view=unread', hasHash: true });
        expect(action.mode).toBe('default');
        expect(action.joinAction).toBe('auto');
    });
});

// ── Brak parametrow ───────────────────────────────────────────────────────────

describe('brak URL params', () => {

    test('zwraca default + auto-join', () => {
        const action = decideStartupAction({ search: '' });
        expect(action.mode).toBe('default');
        expect(action.joinAction).toBe('auto');
    });

    test('nieznany param ignorowany', () => {
        const action = decideStartupAction({ search: '?foo=bar' });
        expect(action.mode).toBe('default');
        expect(action.joinAction).toBe('auto');
    });

    test('?view=rooms bez wiodacego ? (bezposrednio "view=rooms")', () => {
        const action = decideStartupAction({ search: 'view=rooms' });
        expect(action.mode).toBe('rooms');
    });
});
