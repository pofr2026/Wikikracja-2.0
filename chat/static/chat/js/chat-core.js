/**
 * @file chat-core.js
 * Core chat functionality shared between chat.js and chat-embedded.js
 * Contains: input serialization, message formatting, file uploads, reply handling, and Enter key handling
 */

import { _, formatDate, formatTime } from './utility.js';

/**
 * Serialize contenteditable HTML to sanitized HTML string
 * Handles block elements by converting them to <br> tags to preserve newlines
 * @param {HTMLElement} inputEl - The contenteditable element
 * @returns {string} Sanitized HTML
 */
export function getInputHtml(inputEl) {
    if (!inputEl) return '';

    const ALLOWED_TAGS = ['b', 'i', 'u', 'br'];
    const BLOCK = new Set(['DIV', 'P', 'SECTION', 'BLOCKQUOTE', 'LI']);

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
        return inner;
    }

    const html = Array.from(inputEl.childNodes).map((c, i) => serialize(c, i === 0)).join('');
    return (typeof DOMPurify !== 'undefined')
        ? DOMPurify.sanitize(html, { ALLOWED_TAGS, ALLOWED_ATTR: [] })
        : html.replace(/<(?!\/?(?:b|i|u|br)\b)[^>]*>/gi, '');
}

/**
 * Update character counter display
 * @param {HTMLElement} inputEl - The input element (contenteditable or textarea)
 * @param {HTMLElement} counterEl - The counter container element
 * @param {HTMLElement} counterVal - The counter value element
 * @param {HTMLElement} sendBtn - The send button (to disable/enable)
 * @param {number} maxLength - Maximum allowed characters
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
 * Format message with XSS protection and linkification
 * @param {string} raw - Raw message string
 * @returns {string} Formatted HTML string
 */
export function formatMessage(raw) {
    const ALLOWED_TAGS = ['b', 'i', 'u', 'br'];
    const clean = (typeof DOMPurify !== 'undefined')
        ? DOMPurify.sanitize(raw, { ALLOWED_TAGS, ALLOWED_ATTR: [] })
        : raw.replace(/</g, '<').replace(/>/g, '>');
    const URL_REGEX = /https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)/g;
    return clean.replace(URL_REGEX, (url) => {
        const isInternal = url.replace(/^https?/, 'http').startsWith(window.location.origin.replace(/^https?/, 'http'));
        return `<a href="${url}"${isInternal ? '' : ' target="_blank" rel="noopener"'}>${url}</a>`;
    });
}

/**
 * Upload files via XHR
 * @param {FileList|Array} files - Files to upload
 * @param {string} uploadUrl - Upload endpoint URL (default: '/chat/upload/')
 * @returns {Promise<{filenames: string[]}>}
 */
export async function uploadFiles(files, uploadUrl = '/chat/upload/') {
    if (!files || files.length === 0) {
        return { filenames: [] };
    }

    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        const formData = new FormData();

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (file.size > 10000000) {
                alert('File is too big');
                continue;
            }
            formData.append('files', file);
        }

        xhr.onreadystatechange = () => {
            if (xhr.readyState === 4 && xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (e) {
                    reject(e);
                }
            }
        };

        xhr.onerror = () => {
            reject(new Error('Upload failed'));
        };

        xhr.open('POST', uploadUrl, true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        xhr.send(formData);
    });
}

/**
 * Set reply target with preview
 * @param {number} message_id - Message ID being replied to
 * @param {string} username - Username of the message author
 * @param {string} snippet - Snippet of the message being replied to
 * @param {HTMLElement} previewEl - Reply preview container
 * @param {HTMLElement} previewTextEl - Reply preview text element
 * @returns {number} The message_id (for state management by caller)
 */
export function setReplyTarget(message_id, username, snippet, previewEl, previewTextEl) {
    if (previewEl && previewTextEl) {
        previewTextEl.textContent = `${username}: ${snippet}`;
        previewEl.style.display = '';
    }
    return message_id;
}

/**
 * Clear reply target
 * @param {HTMLElement} previewEl - Reply preview container
 * @returns {null} Returns null (for state management by caller)
 */
export function clearReplyTarget(previewEl) {
    if (previewEl) previewEl.style.display = 'none';
    return null;
}

/**
 * Handle Enter key in message input
 * Ctrl+Enter or Cmd+Enter submits, plain Enter adds newline (default behavior)
 * @param {KeyboardEvent} e - Keyboard event
 * @param {Function} submitCallback - Function to call on Ctrl+Enter / Cmd+Enter
 * @returns {boolean} True if the key was handled
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
 * Get visible text length from input element (contenteditable or textarea)
 * @param {HTMLElement} inputEl - The input element
 * @returns {number} Length of visible text
 */
export function getVisibleTextLength(inputEl) {
    if (!inputEl) return 0;
    return inputEl.isContentEditable ? (inputEl.textContent || '').length : (inputEl.value || '').length;
}