from django import forms

from .models import Argument, Decyzja


class DecyzjaForm(forms.ModelForm):
    class Meta:
        model = Decyzja
        fields = ('title', 'tresc', 'uzasadnienie', 'kara', 'znosi')
        widgets = {
            'title': forms.TextInput(),
        }


class ArgumentForm(forms.ModelForm):
    class Meta:
        model = Argument
        fields = ('argument_type', 'content')
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3
            }),
        }
