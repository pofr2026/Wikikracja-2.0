from django import forms

from site_settings.models import SiteSettings


class SiteSettingsBrandingForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['branding_text', 'brand_mark', 'brand_mark_dark']
        widgets = {
            # size= ustawia wizualną szerokość input'a tak by zmieścił max_length znaków bez przewijania
            'branding_text': forms.TextInput(attrs={'size': SiteSettings._meta.get_field('branding_text').max_length}),
        }
