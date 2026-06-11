from django import forms

from home.widgets import RichTextWidget

from .models import Argument, Decyzja


class DecyzjaForm(forms.ModelForm):
    class Meta:
        model = Decyzja
        fields = ('title', 'tresc', 'uzasadnienie', 'kara', 'znosi')
        widgets = {
            'title': forms.TextInput(),
            'tresc': RichTextWidget(max_length=3000),
            'uzasadnienie': RichTextWidget(max_length=2000),
            'kara': RichTextWidget(max_length=500),
        }


class ArgumentForm(forms.ModelForm):
    class Meta:
        model = Argument
        fields = ('argument_type', 'content')
        widgets = {
            # licznik/limit widgetu z modelu — to samo źródło prawdy, którego ModelForm użyje do walidacji
            'content': RichTextWidget(max_length=Argument._meta.get_field('content').max_length),
        }
