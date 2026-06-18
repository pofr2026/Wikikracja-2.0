from django.templatetags.static import static

from site_settings.models import SiteSettings
from site_settings.services import get_branding_asset_url, get_branding_version


def branding(request):
    """Wstrzykuje SiteSettings (logo, brand mark) + version (cache-bust) do każdego template'u."""
    ss = SiteSettings.get()
    if ss.brand_mark:
        asset_urls = {
            'favicon': get_branding_asset_url(ss, 'favicon.ico'),
            'apple_touch_icon': get_branding_asset_url(ss, 'apple-touch-icon.png'),
        }
    else:
        asset_urls = {
            'favicon': static('home/images/favicon.ico'),
            'apple_touch_icon': static('home/images/favicon.ico'),
        }
    return {
        'branding': ss,
        'branding_asset_urls': asset_urls,
        'branding_version': get_branding_version(ss),
    }
