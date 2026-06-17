"""
Shared rich-text sanitization for user-generated content.

Single source of truth for which HTML tags users may submit and how URLs
are auto-linkified. Used by chat (consumers, services) and by the
`|richtext` template filter for tasks/glosowania/events.
"""

import re
from html.parser import HTMLParser

import bleach

ALLOWED_TAGS = ['b', 'i', 'u', 'br', 'a']
ALLOWED_ATTRS = {'a': ['href', 'rel', 'target']}


def _set_link_target(attrs, new=False):
    """bleach.linkify callback: external links open in a new tab."""
    from zzz.utils import get_site_domain
    href = attrs.get((None, 'href'), '')
    domain = get_site_domain()
    is_internal = (
        href.startswith('/')
        or href.startswith(f'http://{domain}')
        or href.startswith(f'https://{domain}')
    )
    if not is_internal:
        attrs[(None, 'target')] = '_blank'
        attrs[(None, 'rel')] = 'noopener'
    return attrs


def sanitize(text: str, *, linkify: bool = True) -> str:
    """Sanitize user HTML, keeping only ALLOWED_TAGS and (optionally) auto-linking URLs.

    Normalizes line endings (CRLF/CR/LF) to <br> — single source of truth so callers
    (chat consumers, RichTextWidget, |richtext filter) don't each carry their own
    replace. Eliminates ghost empty lines from legacy DB content with raw \\n.
    """
    if not text:
        return ''
    normalized = text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>')
    cleaned = bleach.clean(normalized, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    if linkify:
        cleaned = bleach.linkify(cleaned, callbacks=[_set_link_target])
    return cleaned


_TAG_RE = re.compile(r'<[^>]+>')


def strip_tags(text: str) -> str:
    """Remove all HTML tags — for plain-text snippets (notifications, quotes)."""
    return _TAG_RE.sub('', text or '')


class _RichTextContentLengthParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.length = 0
        self._anchors = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'a':
            return
        href = dict(attrs).get('href') or ''
        self._anchors.append({
            'href_len': len(href),
            'text_len': 0,
        })

    def handle_endtag(self, tag):
        if tag.lower() == 'a':
            self._close_anchor()

    def handle_data(self, data):
        data_len = len(data)
        self.length += data_len
        if self._anchors:
            self._anchors[-1]['text_len'] += data_len

    def close(self):
        super().close()
        while self._anchors:
            self._close_anchor()

    def _close_anchor(self):
        if not self._anchors:
            return
        anchor = self._anchors.pop()
        extra_href_len = max(0, anchor['href_len'] - anchor['text_len'])
        self.length += extra_href_len
        if self._anchors:
            self._anchors[-1]['text_len'] += extra_href_len


def richtext_content_length(text: str) -> int:
    """Count rich-text content without double-counting generated link markup."""
    parser = _RichTextContentLengthParser()
    parser.feed(text or '')
    parser.close()
    return parser.length
