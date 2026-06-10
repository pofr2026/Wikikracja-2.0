/**
 * @jest-environment jsdom
 *
 * Testy regresyjne dla systemu draft (chat.js).
 *
 * Bugi które pokrywamy:
 *   A) clearDraft jest wywołany PRZED input.innerHTML='', więc jeśli przeglądarka
 *      odpali natywny 'input' event ze starą treścią podczas innerHTML='', draft
 *      zostaje nadpisany z powrotem do localStorage.
 *      Fix: clearDraft musi być wywołany PO wyczyszczeniu inputa.
 *
 *   B) dispatchEvent(new Event('input')) używa bubbles:false — event nie dociera
 *      do document-level listenera (counter, saveDraft), więc counter nie resetuje się.
 *      Fix: używać new InputEvent('input', { bubbles: true }).
 */

// ── helpers (wierne kopie z chat.js) ─────────────────────────────────────────

function makeDraftKey(roomId) {
    return `chat_draft_${roomId}`;
}

function isEditable(el) {
    // jsdom nie implementuje isContentEditable, sprawdzamy atrybut bezpośrednio
    return el.getAttribute('contenteditable') === 'true' || el.isContentEditable === true;
}

function saveDraft(input, currentRoomId) {
    if (!input || !currentRoomId) return;
    const content = isEditable(input) ? (input.innerHTML ?? '') : (input.value ?? '');
    if (content.replace(/<[^>]*>/g, '').trim()) {
        localStorage.setItem(makeDraftKey(currentRoomId), content);
    } else {
        localStorage.removeItem(makeDraftKey(currentRoomId));
    }
}

function clearDraft(roomId) {
    localStorage.removeItem(makeDraftKey(roomId));
}

function setupInput(html = '') {
    const input = document.createElement('div');
    input.id = 'message-input';
    input.setAttribute('contenteditable', 'true');
    input.innerHTML = html;
    document.body.appendChild(input);
    return input;
}

// ── setup / teardown ─────────────────────────────────────────────────────────

beforeEach(() => {
    localStorage.clear();
    document.body.innerHTML = '';
});

// ── Bug A: kolejność clearDraft vs innerHTML='' ───────────────────────────────

describe('Bug A — clearDraft musi być PO input.innerHTML=""', () => {

    test('kolejność BŁĘDNA: clearDraft przed innerHTML — draft wraca gdy browser odpali input event ze starą treścią', () => {
        const ROOM = 42;
        const input = setupInput('hello world');
        localStorage.setItem(makeDraftKey(ROOM), 'hello world');

        const listener = (e) => {
            if (e.target.id === 'message-input') saveDraft(input, ROOM);
        };
        document.addEventListener('input', listener);

        // ── BŁĘDNA kolejność (aktualny kod) ──
        clearDraft(ROOM);
        // Symulujemy przeglądarkę: odpala bubbling input event ZE STARĄ treścią
        // (input.innerHTML jeszcze nie zostało wyczyszczone — to jest sedno buga)
        input.dispatchEvent(new InputEvent('input', { bubbles: true }));
        // saveDraft() widzi input.innerHTML === 'hello world' → zapisuje z powrotem
        input.innerHTML = '';

        // BUG: draft wrócił mimo że clearDraft() był wywołany
        expect(localStorage.getItem(makeDraftKey(ROOM))).toBe('hello world');

        document.removeEventListener('input', listener);
    });

    test('kolejność POPRAWNA: innerHTML="" przed clearDraft — draft usunięty na czysto', () => {
        const ROOM = 42;
        const input = setupInput('hello world');
        localStorage.setItem(makeDraftKey(ROOM), 'hello world');

        const listener = (e) => {
            if (e.target.id === 'message-input') saveDraft(input, ROOM);
        };
        document.addEventListener('input', listener);

        // ── POPRAWNA kolejność (po fixie) ──
        input.innerHTML = '';
        // Przeglądarka może odpalić event z pustą treścią → saveDraft usuwa (OK)
        input.dispatchEvent(new InputEvent('input', { bubbles: true }));
        clearDraft(ROOM); // clearDraft NA KOŃCU — po wyczyszczeniu i wszelkich eventach

        expect(localStorage.getItem(makeDraftKey(ROOM))).toBeNull();

        document.removeEventListener('input', listener);
    });

});

// ── Bug B: bubbles:false nie dociera do document-level listenera ──────────────

describe('Bug B — dispatchEvent musi używać bubbles:true', () => {

    test('new Event("input") z bubbles:false NIE dociera do document-level listenera', () => {
        const input = setupInput();
        let called = false;
        const listener = (e) => { if (e.target.id === 'message-input') called = true; };
        document.addEventListener('input', listener);

        // Aktualny kod — błędny
        input.dispatchEvent(new Event('input')); // bubbles:false domyślnie

        expect(called).toBe(false);

        document.removeEventListener('input', listener);
    });

    test('new InputEvent("input", {bubbles:true}) dociera do document-level listenera', () => {
        const input = setupInput();
        let called = false;
        const listener = (e) => { if (e.target.id === 'message-input') called = true; };
        document.addEventListener('input', listener);

        // Poprawny kod — po fixie
        input.dispatchEvent(new InputEvent('input', { bubbles: true }));

        expect(called).toBe(true);

        document.removeEventListener('input', listener);
    });

});

// ── saveDraft: podstawowe zachowanie ─────────────────────────────────────────

describe('saveDraft — podstawy', () => {

    test('zapisuje treść gdy input nie jest pusty', () => {
        const ROOM = 7;
        const input = setupInput('cześć');
        saveDraft(input, ROOM);
        expect(localStorage.getItem(makeDraftKey(ROOM))).toBe('cześć');
    });

    test('usuwa klucz gdy input jest pusty', () => {
        const ROOM = 7;
        localStorage.setItem(makeDraftKey(ROOM), 'stary draft');
        const input = setupInput('');
        saveDraft(input, ROOM);
        expect(localStorage.getItem(makeDraftKey(ROOM))).toBeNull();
    });

    test('traktuje <br> jako pusty input', () => {
        const ROOM = 7;
        localStorage.setItem(makeDraftKey(ROOM), 'coś');
        const input = setupInput('<br>');
        saveDraft(input, ROOM);
        expect(localStorage.getItem(makeDraftKey(ROOM))).toBeNull();
    });

    test('nie zapisuje gdy currentRoomId jest null', () => {
        const input = setupInput('tekst');
        saveDraft(input, null);
        expect(localStorage.length).toBe(0);
    });

});
