/**
 * @file richtext-core.js
 * Pure functions for sanitizing/rendering minimal rich text (b/i/u/br + auto-links).
 * Single source of truth shared by chat input and form RichTextWidget.
 *
 * Allowed tags must stay in sync with `zzz/richtext.py::ALLOWED_TAGS` on the backend.
 */

const ALLOWED_TAGS = ['b', 'i', 'u', 'br', 'a'];
const ALLOWED_ATTR = ['href', 'rel', 'target'];

/**
 * Serialize contenteditable HTML to sanitized HTML string.
 * Block elements (DIV/P/SECTION/...) are converted to <br> to preserve newlines.
 * @param {HTMLElement} inputEl
 * @returns {string}
 */
export function getInputHtml(inputEl) {
    if (!inputEl) return '';

    const BLOCK = new Set(['DIV', 'P', 'SECTION', 'BLOCKQUOTE', 'LI']);

    function escapeAttr(s) {
        return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
    }

    function serialize(node, isFirst) {
        if (node.nodeType === Node.TEXT_NODE) return node.textContent;
        if (node.nodeType !== Node.ELEMENT_NODE) return '';
        const tag = node.tagName.toUpperCase();
        if (tag === 'BR') return '<br>';
        const inner = Array.from(node.childNodes).map((c, i) => serialize(c, i === 0)).join('');
        if (BLOCK.has(tag)) return (isFirst ? '' : '<br>') + inner;
        if (tag === 'B') return `<b>${inner}</b>`;
        if (tag === 'I') return `<i>${inner}</i>`;
        if (tag === 'U') return `<u>${inner}</u>`;
        if (tag === 'A') {
            const href = node.getAttribute('href') || '';
            return `<a href="${escapeAttr(href)}">${inner}</a>`;
        }
        return inner;
    }

    const html = Array.from(inputEl.childNodes).map((c, i) => serialize(c, i === 0)).join('');
    return (typeof DOMPurify !== 'undefined')
        ? DOMPurify.sanitize(html, { ALLOWED_TAGS, ALLOWED_ATTR })
        : html.replace(/<(?!\/?(?:b|i|u|br|a)\b)[^>]*>/gi, '');
}

/**
 * Sanitize HTML for display + auto-linkify plain URLs.
 * @param {string} raw
 * @returns {string}
 */
export function formatMessage(raw) {
    const clean = (typeof DOMPurify !== 'undefined')
        ? DOMPurify.sanitize(raw, { ALLOWED_TAGS, ALLOWED_ATTR })
        : String(raw ?? '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    // Linkify only URLs that are not already inside an <a> element.
    const URL_REGEX = /(?:<a\b[^>]*>[^<]*<\/a>)|(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*))/g;
    return clean.replace(URL_REGEX, (match, url) => {
        if (!url) return match; // pre-existing <a>...</a>, leave untouched
        const isInternal = url.replace(/^https?/, 'http').startsWith(window.location.origin.replace(/^https?/, 'http'));
        return `<a href="${url}"${isInternal ? '' : ' target="_blank" rel="noopener"'}>${url}</a>`;
    });
}

/**
 * Update char counter UI for an input element.
 * @param {HTMLElement} inputEl
 * @param {HTMLElement} counterEl
 * @param {HTMLElement} counterVal
 * @param {HTMLButtonElement} sendBtn
 * @param {number} maxLength
 */
export function updateCounter(inputEl, counterEl, counterVal, sendBtn, maxLength) {
    const len = (inputEl?.textContent || '').length;
    const rem = maxLength - len;
    if (counterVal) counterVal.textContent = rem;
    if (!counterEl) return;
    counterEl.classList.remove('counter--warn', 'counter--error');
    if (rem <= 0 || rem <= 10) counterEl.classList.add('counter--error');
    else if (rem <= 50) counterEl.classList.add('counter--warn');
    if (sendBtn) sendBtn.disabled = rem <= 0;
}

/**
 * Ctrl+Enter / Cmd+Enter submits, plain Enter passes through.
 * @returns {boolean} true if handled
 */
export function handleEnterKey(e, submitCallback) {
    const mod = e.ctrlKey || e.metaKey;
    if (e.key === 'Enter' && mod) {
        e.preventDefault();
        submitCallback();
        return true;
    }
    return false;
}

/**
 * Visible text length for either contenteditable or textarea.
 * @returns {number}
 */
export function getVisibleTextLength(inputEl) {
    if (!inputEl) return 0;
    return inputEl.isContentEditable ? (inputEl.textContent || '').length : (inputEl.value || '').length;
}

let _pasteHandlerReady = false;

/**
 * Global clipboard image paste handler for all .message-input-rich elements.
 * Detects image in clipboard → injects into nearest .file-input within the same
 * .compose-box → triggers existing file preview/upload pipeline via change event.
 * Safe to call from multiple modules — registers only once.
 */
export function initGlobalPasteImageHandler() {
    if (_pasteHandlerReady) return;
    _pasteHandlerReady = true;
    document.addEventListener('paste', (e) => {
        if (!e.target.classList.contains('message-input-rich')) return;
        const imageItem = Array.from(e.clipboardData?.items ?? []).find(it => it.type.startsWith('image/'));
        if (!imageItem) return;
        e.preventDefault();
        const blob = imageItem.getAsFile();
        if (!blob) return;
        const fileInput = e.target.closest('.compose-box')?.querySelector('.file-input');
        if (!fileInput) return;
        const ext = blob.type.split('/')[1]?.split('+')[0] || 'png';
        const dt = new DataTransfer();
        // Preserve existing files so pasted images append rather than replace.
        for (const f of fileInput.files || []) dt.items.add(f);
        dt.items.add(new File([blob], `paste-${Date.now()}.${ext}`, { type: blob.type }));
        fileInput.files = dt.files;
        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
    });
}
