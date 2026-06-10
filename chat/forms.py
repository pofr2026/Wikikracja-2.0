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
            title_cf = title.casefold()
            qs = Room.objects.values_list('title', 'pk')
            existing = next(
                (pk for t, pk in qs if t.casefold() == title_cf
                 and (not self.instance or not self.instance.pk or pk != self.instance.pk)),
                None,
            )
            if existing is not None:
                raise ValidationError("Pokój o tej nazwie już istnieje.", code='duplicate_title')
        return title
