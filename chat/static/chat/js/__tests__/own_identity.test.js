/**
 * @jest-environment jsdom
 *
 * Testy getOwnIdentity — odczyt wlasnego avatara i user_id z navbara (.sidebar-user).
 * Uzywane przez optimistic render wlasnej wiadomosci, zeby balbelek od razu mial
 * avatar + link do profilu (bez czekania na echo z serwera / bez migotania).
 *
 * Zrodlo w DOM: home/base.html — .sidebar-user (link /obywatele/<pk>/) zawiera
 * albo <img class="user-avatar"> (avatar), albo <div class="user-avatar"> (inicjaly).
 *
 * DLACZEGO kopia 1:1 zamiast importu: jest.config.js ma `transform: {}` (brak
 * Babel/ts-jest), a utility.js to ES module (`export function`). `import` z niego
 * rzuca "Cannot use import statement outside a module". Caly ten katalog testow
 * trzyma sie wiec wzorca kopiowania funkcji do testu i synchronizacji recznej —
 * patrz sidebar_update.test.js. Przy zmianie utility.js zaktualizuj te kopie.
 */

// ── wierna kopia z utility.js (synchronizowac przy zmianie!) ───────────────
function getOwnIdentity() {
    const card = document.querySelector('.sidebar-user');
    if (!card) return { avatarUrl: null, userId: null };

    const img = card.querySelector('img.user-avatar');
    const avatarUrl = img ? img.getAttribute('src') : null;

    const href = card.getAttribute('href') || '';
    const match = href.match(/\/obywatele\/(\d+)\//);
    const userId = match ? Number(match[1]) : null;

    return { avatarUrl, userId };
}

// ── helpers ────────────────────────────────────────────────────────────────
function mountUserCard({ withAvatar, userId = 42 }) {
    const inner = withAvatar
        ? `<img class="user-avatar" src="/media/uploads/avatar.png" alt="avatar">`
        : `<div class="user-avatar">AB</div>`;
    document.body.innerHTML = `
        <a href="/obywatele/${userId}/" class="sidebar-user">
            ${inner}
            <div class="user-info"><span class="user-name">Alice</span></div>
        </a>`;
}

// ── testy ──────────────────────────────────────────────────────────────────
describe('getOwnIdentity', () => {
    test('avatar jako <img>: zwraca src i user_id z href', () => {
        mountUserCard({ withAvatar: true, userId: 7 });
        expect(getOwnIdentity()).toEqual({ avatarUrl: '/media/uploads/avatar.png', userId: 7 });
    });

    test('avatar jako inicjaly (<div>): avatarUrl=null, user_id nadal odczytany', () => {
        mountUserCard({ withAvatar: false, userId: 7 });
        expect(getOwnIdentity()).toEqual({ avatarUrl: null, userId: 7 });
    });

    test('brak .sidebar-user w DOM: bezpieczny fallback null/null', () => {
        document.body.innerHTML = '<div>no user card here</div>';
        expect(getOwnIdentity()).toEqual({ avatarUrl: null, userId: null });
    });
});

// ── wybor tozsamosci wg is_anonymous (kontrakt z chat.js onSubmitMessage) ──
// Wierna kopia gałęzi z chat.js:1101-1103 — anonimowa wiadomosc NIE moze wyciekac
// avatara/linku do profilu nadawcy, zwykla przekazuje realna tozsamosc.
// Najlatwiejsze do regresji przy refaktorze, stad osobny test tej galezi.
function pickOwnIdentity(is_anonymous) {
    return is_anonymous
        ? { avatarUrl: null, userId: null }
        : getOwnIdentity();
}

describe('pickOwnIdentity (galaz is_anonymous w onSubmitMessage)', () => {
    beforeEach(() => mountUserCard({ withAvatar: true, userId: 7 }));

    test('zwykla wiadomosc: przekazuje realny avatar i user_id', () => {
        expect(pickOwnIdentity(false)).toEqual({ avatarUrl: '/media/uploads/avatar.png', userId: 7 });
    });

    test('anonimowa wiadomosc: null/null nawet gdy karta ma avatar', () => {
        expect(pickOwnIdentity(true)).toEqual({ avatarUrl: null, userId: null });
    });
});
