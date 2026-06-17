"""
Testy dla zzz/richtext.py — centralna sanityzacja user HTML.

Bug pokrywany: stare wpisy w DB (sprzed JS fix paste) mogą mieć surowe \\n
w wartości. Sanitize musi je normalizować na <br>, żeby render w |richtext
filter / RichTextWidget initial value nie produkował ghost empty lines.
"""

from django.test import TestCase

from zzz.richtext import richtext_content_length, sanitize, strip_tags


class SanitizeNormalizesNewlinesTests(TestCase):
    """\\n w wejściu musi stać się <br> w wyjściu."""

    def test_lone_lf_becomes_br(self):
        self.assertEqual(sanitize('A\nB', linkify=False), 'A<br>B')

    def test_crlf_becomes_br(self):
        self.assertEqual(sanitize('A\r\nB', linkify=False), 'A<br>B')

    def test_cr_alone_becomes_br(self):
        self.assertEqual(sanitize('A\rB', linkify=False), 'A<br>B')

    def test_mixed_br_and_newline(self):
        # Legacy content: <br> already present, \n powinno też być znormalizowane.
        self.assertEqual(
            sanitize('A<br>B\nC', linkify=False),
            'A<br>B<br>C',
        )

    def test_newline_inside_bold(self):
        self.assertEqual(
            sanitize('<b>A\nB</b>', linkify=False),
            '<b>A<br>B</b>',
        )

    def test_empty_input_returns_empty(self):
        self.assertEqual(sanitize('', linkify=False), '')
        self.assertEqual(sanitize(None, linkify=False), '')

    def test_no_newlines_unchanged(self):
        self.assertEqual(sanitize('A<br>B', linkify=False), 'A<br>B')


class SanitizeKeepsAllowedTagsTests(TestCase):
    """Regresja — fix \\n nie może złamać whitelistu tagów."""

    def test_allowed_tags_survive(self):
        self.assertEqual(
            sanitize('<b>x</b><i>y</i><u>z</u><br>', linkify=False),
            '<b>x</b><i>y</i><u>z</u><br>',
        )

    def test_disallowed_tags_stripped(self):
        # <script> stripped, content kept (strip=True w bleach)
        self.assertEqual(
            sanitize('<script>alert(1)</script>A', linkify=False),
            'alert(1)A',
        )

    def test_newline_in_href_attribute_does_not_crash(self):
        # Edge case: \n w atrybucie href (np. z import/migration legacy data).
        # Bleach powinno zachować bezpieczny output — żadnego crashu, tekst zachowany.
        result = sanitize('<a href="http://example.com\nfoo">text</a>', linkify=False)
        self.assertIn('text', result)
        self.assertNotIn('<script', result.lower())

    def test_newline_between_tags_normalized(self):
        # \n między tagami (typowy whitespace formatowania w legacy content).
        self.assertEqual(
            sanitize('<b>A</b>\n<b>B</b>', linkify=False),
            '<b>A</b><br><b>B</b>',
        )


class StripTagsTests(TestCase):
    """Sanity check — strip_tags pozostaje bez zmian."""

    def test_strips_all_tags(self):
        self.assertEqual(strip_tags('<b>a</b><br><i>b</i>'), 'ab')

    def test_empty(self):
        self.assertEqual(strip_tags(''), '')
        self.assertEqual(strip_tags(None), '')


class RichTextContentLengthTests(TestCase):
    def test_autolinked_url_is_counted_once(self):
        url = 'https://example.com/source'
        html = f'<a href="{url}" target="_blank" rel="noopener">{url}</a>'

        self.assertEqual(richtext_content_length(html), len(url))

    def test_hidden_href_longer_than_label_counts_toward_limit(self):
        href = 'https://example.com/' + ('a' * 80)
        html = f'<a href="{href}">x</a>'

        self.assertEqual(richtext_content_length(html), len(href))
