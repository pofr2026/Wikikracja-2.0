/**
 * @jest-environment jsdom
 */
const fs = require('fs');
const path = require('path');

const APP_JS_PATH = path.join(__dirname, '..', 'app.js');

function loadAppScript() {
    const src = fs.readFileSync(APP_JS_PATH, 'utf8');
    const run = new Function(src);
    run();
}

function createExpandable() {
    document.body.innerHTML = `
        <div class="expandable has-overflow">
            <div class="expandable-body">To jest dluzszy tekst do zaznaczania.</div>
        </div>
    `;
    return {
        wrapper: document.querySelector('.expandable'),
        body: document.querySelector('.expandable-body'),
    };
}

describe('expandable toggle click handler', () => {
    beforeAll(() => {
        loadAppScript();
    });

    beforeEach(() => {
        document.body.innerHTML = '';
        window.getSelection()?.removeAllRanges();
    });

    test('toggles expandable on normal click', () => {
        const { wrapper, body } = createExpandable();
        body.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(wrapper.classList.contains('is-open')).toBe(true);
    });

    test('does not toggle when text is selected in expandable body', () => {
        const { wrapper, body } = createExpandable();
        const textNode = body.firstChild;
        const range = document.createRange();
        range.setStart(textNode, 0);
        range.setEnd(textNode, 4);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);

        body.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(wrapper.classList.contains('is-open')).toBe(false);
    });

    test('does not toggle when selection crosses expandable body boundary', () => {
        document.body.innerHTML = `
            <div class="message">
                <span class="outside">Poczatek wiadomosci </span>
                <div class="expandable has-overflow">
                    <div class="expandable-body">Szczegoly ktore mozna rozwinac.</div>
                </div>
            </div>
        `;
        const wrapper = document.querySelector('.expandable');
        const body = document.querySelector('.expandable-body');
        const outsideTextNode = document.querySelector('.outside').firstChild;
        const bodyTextNode = body.firstChild;
        const range = document.createRange();
        range.setStart(outsideTextNode, 3);
        range.setEnd(bodyTextNode, 8);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);

        body.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(wrapper.classList.contains('is-open')).toBe(false);
    });
});
