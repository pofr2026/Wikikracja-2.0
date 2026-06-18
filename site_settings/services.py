import os

from django.conf import settings
from django.core.cache import cache
from django.templatetags.static import static
from PIL import Image

DERIVED_SUBDIR = 'site_branding/derived'
FAVICON_REDIRECT_CACHE_KEY = 'site_settings:favicon_redirect_url:v1'
FAVICON_REDIRECT_CACHE_TTL = 300
FAVICON_REDIRECT_CACHE_CONTROL = f'public, max-age={FAVICON_REDIRECT_CACHE_TTL}'

# wymiary PNG derivatives — używane przez przeglądarki/iOS/Android/PWA
PNG_DERIVATIVES = {
    'apple-touch-icon.png': 180,  # iOS Safari "Dodaj do ekranu głównego"
    'icon-192.png': 192,           # Android PWA install
    'icon-512.png': 512,           # PWA splash screen
}
FAVICON_SIZES = [(16, 16), (32, 32), (48, 48)]  # multi-size ICO


def regenerate_brand_derivatives(site_settings):
    """Generuje favicon.ico + apple-touch-icon + PWA icons z brand_mark."""
    if not site_settings.brand_mark:
        return

    derived_dir = os.path.join(settings.MEDIA_ROOT, DERIVED_SUBDIR)
    os.makedirs(derived_dir, exist_ok=True)

    with Image.open(site_settings.brand_mark.path) as img:
        # konwersja na RGBA chroni przed plikami bez alpha (np. JPG) — derivatives zawsze z przezroczystością
        rgba = img.convert('RGBA')

        for filename, size in PNG_DERIVATIVES.items():
            resized = rgba.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(os.path.join(derived_dir, filename), format='PNG')

        # multi-size ICO — Pillow natywnie generuje wszystkie rozmiary z listy
        rgba.save(os.path.join(derived_dir, 'favicon.ico'), format='ICO', sizes=FAVICON_SIZES)


def letterbox_to_square(file_path):
    """Letterboxuje obraz do kwadratu max(w,h)×max(w,h) z transparentnym tłem, nadpisując plik jako PNG.

    Prostokąt → kwadrat: oryginał na środku, dookoła transparentne tło.
    Kwadrat → bez zmian (skip).
    """
    with Image.open(file_path) as img:
        width, height = img.size
        if width == height:
            return
        side = max(width, height)
        rgba = img.convert('RGBA')

    canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    canvas.paste(rgba, ((side - width) // 2, (side - height) // 2))
    canvas.save(file_path, format='PNG')


def cleanup_brand_derivatives(site_settings):
    """Usuwa wygenerowane derivatives faviconu/PWA z dysku — wołane gdy brand_mark zostaje wyczyszczony."""
    derived_dir = os.path.join(settings.MEDIA_ROOT, DERIVED_SUBDIR)
    if not os.path.isdir(derived_dir):
        return
    for filename in (*PNG_DERIVATIVES.keys(), 'favicon.ico'):
        path = os.path.join(derived_dir, filename)
        if os.path.isfile(path):
            os.remove(path)


def get_branding_version(site_settings):
    """Zwraca unix timestamp z updated_at jako string — query param dla cache-busting."""
    if site_settings.updated_at:
        return str(int(site_settings.updated_at.timestamp()))
    return '0'


def get_branding_asset_url(site_settings, filename):
    """Build a cache-busted URL for a generated branding derivative."""
    return f'{settings.MEDIA_URL}{DERIVED_SUBDIR}/{filename}?v={get_branding_version(site_settings)}'


def get_favicon_redirect_url():
    """Return the /favicon.ico redirect target without hitting the DB on every request."""
    cached = cache.get(FAVICON_REDIRECT_CACHE_KEY)
    if cached is not None:
        return cached

    from site_settings.models import SiteSettings
    site_settings = SiteSettings.get()
    if site_settings.brand_mark:
        favicon_url = get_branding_asset_url(site_settings, 'favicon.ico')
    else:
        favicon_url = static('home/images/favicon.ico')

    cache.set(FAVICON_REDIRECT_CACHE_KEY, favicon_url, FAVICON_REDIRECT_CACHE_TTL)
    return favicon_url


def invalidate_branding_asset_url_cache():
    cache.delete(FAVICON_REDIRECT_CACHE_KEY)
