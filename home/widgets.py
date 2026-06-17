from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from zzz.richtext import richtext_content_length, sanitize

TOOLBAR_HTML = mark_safe(
    '<div class="fmt-toolbar">'
    '<button class="fmt-btn" type="button" data-cmd="bold" title="Ctrl+B"><b>B</b></button>'
    '<button class="fmt-btn" type="button" data-cmd="italic" title="Ctrl+I"><i>I</i></button>'
    '<button class="fmt-btn" type="button" data-cmd="underline" title="Ctrl+U"><u>U</u></button>'
    '</div>'
)

# Bleach autolinks duplicate each URL into href plus anchor markup. Short,
# URL-heavy valid content can exceed 5x the visible length, so keep an 8x
# backstop for tag bloat without rejecting text that the counter accepts.
RICHTEXT_HTML_MAX_LENGTH_MULTIPLIER = 8


class RichTextWidget(forms.Textarea):
    """
    Form widget that renders a contenteditable rich-text input with a B/I/U
    toolbar matching the chat composer. The contenteditable's HTML is mirrored
    into a hidden <input> so the form posts back exactly the same data shape
    as a regular Textarea.

    Allowed tags are defined centrally in `zzz.richtext.ALLOWED_TAGS`.
    """

    class Media:
        # DOMPurify is loaded globally by home/base.html (used by both chat and
        # this widget), so we only declare the widget-specific JS here.
        js = (
            'common/js/richtext-input.js',
        )
        css = {
            'all': ('chat/css/chat.css',),
        }

    def __init__(self, attrs=None, max_length=None, placeholder=''):
        super().__init__(attrs)
        self.max_length = max_length
        self.placeholder = placeholder

    def render(self, name, value, attrs=None, renderer=None):
        value = value or ''
        initial_html = sanitize(str(value), linkify=True)  # already safe HTML

        wrapper_attrs = (
            format_html(' data-max-length="{}"', int(self.max_length))
            if self.max_length else ''
        )
        placeholder_attr = (
            format_html(' data-placeholder="{}"', self.placeholder)
            if self.placeholder else ''
        )
        counter = (
            format_html(
                '<div class="msg-counter"><span class="msg-counter-val">{0}</span> / {0}</div>',
                int(self.max_length),
            )
            if self.max_length else ''
        )
        hidden = format_html('<input type="hidden" name="{}" value="{}">', name, value)
        editable_open = format_html(
            '<div class="richtext-input message-input-rich" contenteditable="true"'
            ' role="textbox" aria-multiline="true"{}>',
            placeholder_attr,
        )
        wrapper_open = format_html('<div class="richtext-wrapper" data-richtext{}>', wrapper_attrs)

        return mark_safe(
            f'{wrapper_open}{TOOLBAR_HTML}{editable_open}{initial_html}</div>{hidden}{counter}</div>'
        )

    def value_from_datadict(self, data, files, name):
        # JS keeps the hidden <input name="..."> in sync, so the standard
        # Textarea/CharField data path Just Works. Run sanitize as defense in
        # depth: if JS is disabled or POST is crafted manually, we still strip
        # disallowed tags before the value reaches the form's clean step.
        raw = data.get(name, '')
        return sanitize(raw, linkify=True) if raw else raw


class RichTextFormField(forms.CharField):
    """CharField variant whose max_length applies to rich-text content."""

    def __init__(self, *args, max_length=None, html_max_length=None, **kwargs):
        self.visible_max_length = max_length
        if html_max_length is None and max_length is not None:
            # Linkified URLs add anchor markup around visible text. Keep enough
            # headroom for URL-heavy valid content, but still bound markup bloat.
            html_max_length = max_length * RICHTEXT_HTML_MAX_LENGTH_MULTIPLIER
        self.html_max_length = html_max_length
        super().__init__(*args, max_length=None, **kwargs)
        # Keep field.max_length available for templates/introspection; validation
        # below applies it to visible rich-text content instead of raw HTML.
        self.max_length = max_length

    def to_python(self, value):
        value = super().to_python(value)
        if value and richtext_content_length(value) == 0:
            return ''
        return value

    def validate(self, value):
        super().validate(value)
        content_length = richtext_content_length(value)
        if self.visible_max_length is not None and content_length > self.visible_max_length:
            raise ValidationError(
                MaxLengthValidator.message,
                code='max_length',
                params={
                    'limit_value': self.visible_max_length,
                    'show_value': content_length,
                },
            )
        html_length = len(value or '')
        if self.html_max_length is not None and html_length > self.html_max_length:
            raise ValidationError(
                MaxLengthValidator.message,
                code='max_length',
                params={
                    'limit_value': self.html_max_length,
                    'show_value': html_length,
                },
            )
