from django.test import TestCase

from glosowania.forms import ArgumentForm, DecyzjaForm
from zzz.richtext import sanitize


class DecyzjaFormRichTextLimitTests(TestCase):
    def test_law_text_limit_counts_visible_text_not_link_markup(self):
        visible_text = ('a' * 2975) + ' https://example.com'
        submitted_html = sanitize(visible_text, linkify=True)

        self.assertLessEqual(len(visible_text), 3000)
        self.assertGreater(len(submitted_html), 3000)

        form = DecyzjaForm(data={
            'title': 'Test',
            'tresc': submitted_html,
            'uzasadnienie': 'Uzasadnienie',
            'kara': '',
            'znosi': '',
        })

        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_law_text_allows_max_visible_text_with_long_url(self):
        url = 'https://example.com/' + ('a' * 1000)
        visible_text = ('a' * (3000 - len(url) - 1)) + ' ' + url
        submitted_html = sanitize(visible_text, linkify=True)

        self.assertEqual(len(visible_text), 3000)
        self.assertGreater(len(submitted_html), 3750)

        form = DecyzjaForm(data={
            'title': 'Test',
            'tresc': submitted_html,
            'uzasadnienie': 'Uzasadnienie',
            'kara': '',
            'znosi': '',
        })

        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_law_text_allows_visible_text_with_many_urls(self):
        urls = [f'https://example.com/{i:02d}' for i in range(60)]
        url_text = ' '.join(urls)
        visible_text = ('a' * (2524 - len(url_text) - 1)) + ' ' + url_text
        submitted_html = sanitize(visible_text, linkify=True)

        self.assertEqual(len(visible_text), 2524)
        self.assertGreater(len(submitted_html), 3750)

        form = DecyzjaForm(data={
            'title': 'Test',
            'tresc': submitted_html,
            'uzasadnienie': 'Uzasadnienie',
            'kara': '',
            'znosi': '',
        })

        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_law_text_allows_visible_limit_with_many_short_urls(self):
        visible_text = ' '.join(['https://x.co'] * 230)
        submitted_html = sanitize(visible_text, linkify=True)

        self.assertEqual(len(visible_text), 2989)
        self.assertGreater(len(submitted_html), 15000)

        form = DecyzjaForm(data={
            'title': 'Test',
            'tresc': submitted_html,
            'uzasadnienie': 'Uzasadnienie',
            'kara': '',
            'znosi': '',
        })

        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_law_text_visible_text_still_enforces_max_length(self):
        form = DecyzjaForm(data={
            'title': 'Test',
            'tresc': 'a' * 3001,
            'uzasadnienie': 'Uzasadnienie',
            'kara': '',
            'znosi': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('tresc', form.errors)

    def test_law_text_limit_counts_hidden_href_when_label_is_shorter(self):
        href = 'https://example.com/' + ('a' * 3000)
        form = DecyzjaForm(data={
            'title': 'Test',
            'tresc': f'<a href="{href}">x</a>',
            'uzasadnienie': 'Uzasadnienie',
            'kara': '',
            'znosi': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('tresc', form.errors)

    def test_law_text_rejects_empty_markup(self):
        form = DecyzjaForm(data={
            'title': 'Test',
            'tresc': '<b></b>' * 1000,
            'uzasadnienie': 'Uzasadnienie',
            'kara': '',
            'znosi': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('tresc', form.errors)

    def test_optional_penalty_normalizes_empty_markup(self):
        form = DecyzjaForm(data={
            'title': 'Test',
            'tresc': 'Law text',
            'uzasadnienie': 'Uzasadnienie',
            'kara': '<b></b>',
            'znosi': '',
        })

        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data['kara'], '')

    def test_optional_penalty_normalizes_large_empty_markup(self):
        form = DecyzjaForm(data={
            'title': 'Test',
            'tresc': 'Treść przepisu',
            'uzasadnienie': 'Uzasadnienie',
            'kara': '<br>' * 1000,
            'znosi': '',
        })

        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data['kara'], '')


class ArgumentFormRichTextLimitTests(TestCase):
    def test_argument_content_uses_visible_limit_and_exposes_max_length(self):
        visible_text = ('a' * 1975) + ' https://example.com'
        submitted_html = sanitize(visible_text, linkify=True)

        self.assertEqual(ArgumentForm().fields['content'].max_length, 2000)
        self.assertLessEqual(len(visible_text), 2000)
        self.assertGreater(len(submitted_html), 2000)

        form = ArgumentForm(data={
            'argument_type': 'FOR',
            'content': submitted_html,
        })

        self.assertTrue(form.is_valid(), form.errors.as_json())
