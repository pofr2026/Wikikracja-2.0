from django import forms

from home.widgets import RichTextFormField, RichTextWidget

from .models import Argument, Decyzja


def _richtext_model_field(model, field_name):
    model_field = model._meta.get_field(field_name)
    return RichTextFormField(
        label=model_field.verbose_name,
        help_text=model_field.help_text,
        required=not model_field.blank,
        max_length=model_field.max_length,
        widget=RichTextWidget(max_length=model_field.max_length),
    )


class DecyzjaForm(forms.ModelForm):
    tresc = _richtext_model_field(Decyzja, 'tresc')
    uzasadnienie = _richtext_model_field(Decyzja, 'uzasadnienie')
    kara = _richtext_model_field(Decyzja, 'kara')

    class Meta:
        model = Decyzja
        fields = ('title', 'tresc', 'uzasadnienie', 'kara', 'znosi')
        widgets = {
            'title': forms.TextInput(),
        }


class ArgumentForm(forms.ModelForm):
    content = _richtext_model_field(Argument, 'content')

    class Meta:
        model = Argument
        fields = ('argument_type', 'content')
