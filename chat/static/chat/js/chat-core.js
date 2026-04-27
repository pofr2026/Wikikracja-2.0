/**
 * @file chat-core.js
 * Core chat functionality shared between chat.js and chat-embedded.js
 * Contains: input serialization, message formatting, file uploads, reply handling, and Enter key handling
 */


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

/**
 * Create a delegated vote handler for message vote buttons
 * @param {Function} sendVote - Callback (eventName, messageId, isAdd) => void
 * @returns {Function} Event handler (e) => void
 */
export function createVoteHandler(sendVote) {
    return function(e) {
        const btn = e.target.closest('.msg-vote');
        if (!btn) return;
        const eventName = btn.dataset.eventName;
        const messageId = btn.dataset.messageId;
        if (!eventName || !messageId) return;
        const isAdd = !btn.classList.contains('active');
        sendVote(eventName, messageId, isAdd);
    };
}

/**
 * Create a delegated reaction handler for message reaction buttons
 * @param {Function} sendReaction - Callback (reaction, messageId) => void
 * @returns {Function} Event handler (e) => void
 */
export function createReactionHandler(sendReaction) {
    return function(e) {
        const btn = e.target.closest('.reaction-btn');
        if (!btn) return;
        const reaction = btn.dataset.reaction;
        const messageId = btn.dataset.messageId;
        if (!reaction || !messageId) return;
        sendReaction(reaction, parseInt(messageId, 10));
    };
}

/**
 * Create a delegated reply handler for reply buttons
 * @param {Function} setReplyTarget - (messageId, username, snippet, previewEl, previewTextEl) => void
 * @param {HTMLElement} replyPreview - Reply preview container
 * @param {HTMLElement} replyPreviewText - Reply preview text element
 * @param {HTMLElement} inputEl - Message input element
 * @returns {Function} Event handler (e) => void
 */
export function createReplyHandler(setReplyTarget, replyPreview, replyPreviewText, inputEl) {
    return function(e) {
        const replyBtn = e.target.closest('.reply-btn');
        if (!replyBtn) return;
        const messageId = replyBtn.dataset.messageId;
        const username = replyBtn.dataset.username;
        const snippet = replyBtn.dataset.snippet;
        if (!messageId) return;
        setReplyTarget(messageId, username, snippet, replyPreview, replyPreviewText);
        if (inputEl) inputEl.focus();
    };
}

/**
 * Create a delegated edit handler for edit buttons
 * @param {Function} startEdit - (messageId, inputEl) => void
 * @param {HTMLElement} inputEl - Message input element
 * @returns {Function} Event handler (e) => void
 */
export function createEditHandler(startEdit, inputEl) {
    return function(e) {
        const editBtn = e.target.closest('.edit-message');
        if (!editBtn) return;
        const messageId = editBtn.dataset.messageId;
        if (!messageId) return;
        startEdit(messageId, inputEl);
    };
}

/**
 * Create a delegated quote jump handler for quote links
 * @param {HTMLElement} messagesContainer - Container with messages
 * @returns {Function} Event handler (e) => void
 */
export function createQuoteJumpHandler(messagesContainer, onJump = undefined) {
    return function(e) {
        const jumpBtn = e.target.closest('.msg-quote-jump') || e.target.closest('.msg-quote');
        if (!jumpBtn) return;
        const targetId = jumpBtn.dataset.targetId || jumpBtn.dataset.replyId
            || jumpBtn.closest('.msg-quote')?.dataset.replyId;
        if (!targetId) return;
        const targetMsg = messagesContainer.querySelector(`.message[data-message-id="${targetId}"]`);
        if (targetMsg) {
            targetMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });
            targetMsg.classList.remove('msg-highlighted');
            void targetMsg.offsetWidth;
            targetMsg.classList.add('msg-highlighted');
            setTimeout(() => targetMsg.classList.remove('msg-highlighted'), 2000);
        }
        if (onJump) onJump(jumpBtn, targetId, targetMsg);
    };
}

/**
 * Create delegated handlers for copy room/message link buttons
 * @param {Function} copyRoomLink - (roomId, button) => void
 * @param {Function} copyMessageLink - (roomId, messageId, button) => void
 * @returns {Object} { roomLinkHandler, messageLinkHandler }
 */
export function createCopyLinkHandler(copyRoomLink, copyMessageLink) {
    return {
        roomLinkHandler: function(e) {
            const btn = e.target.closest('.copy-room-url');
            if (!btn) return;
            const roomId = btn.dataset.roomId;
            if (!roomId) return;
            copyRoomLink(roomId, btn);
        },
        messageLinkHandler: function(e) {
            const btn = e.target.closest('.copy-message-url');
            if (!btn) return;
            const roomId = btn.dataset.roomId;
            const messageId = btn.dataset.messageId;
            if (!roomId || !messageId) return;
            copyMessageLink(roomId, messageId, btn);
        }
    };
}

/**
 * Create a delegated history handler for history buttons
 * @param {Function} showHistory - (messageId) => void
 * @returns {Function} Event handler (e) => void
 */
export function createHistoryHandler(showHistory) {
    return function(e) {
        const btn = e.target.closest('.show-history');
        if (!btn) return;
        const messageId = btn.dataset.messageId;
        if (!messageId) return;
        showHistory(messageId);
    };
}

/**
 * Create a file upload handler for file inputs
 * @param {Function} handleFiles - (files, previewContainer, previewImagesDiv) => void
 * @param {HTMLElement} previewContainer - Preview container element
 * @param {HTMLElement} previewImagesDiv - Preview images container
 * @returns {Function} Event handler (e) => void
 */
export function createFileUploadHandler(handleFiles, previewContainer, previewImagesDiv) {
    return function(e) {
        if (!e.target.classList.contains('file-input')) return;
        const files = e.target.files;
        if (!files || files.length === 0) return;
        handleFiles(files, previewContainer, previewImagesDiv);
    };
}
