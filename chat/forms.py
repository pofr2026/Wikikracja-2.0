from django import forms
from django.core.exceptions import ValidationError

from .models import Room


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        # fields = ('title', 'allowed',)
        fields = ('title',)

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            qs = Room.objects.filter(title=title)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("Pokój o tej nazwie już istnieje.", code='duplicate_title')
        return title
