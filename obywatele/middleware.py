from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.utils import translation

User = get_user_model()


class UserLanguageMiddleware:
    """
    Activates the language saved in the user's profile (Uzytkownik.language).
    Runs after LocaleMiddleware so it can override the auto-detected language
    for authenticated users who have set an explicit preference.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                lang = request.user.uzytkownik.language
                if lang:
                    translation.activate(lang)
                    request.LANGUAGE_CODE = lang
            except Exception:
                pass
        return self.get_response(request)


class UpdateLastSeenMiddleware:
    """
    Aktualizuje user.last_login przy kazdym requescie zalogowanego usera,
    ale max raz na 5 min (throttling przez cache).

    Django domyslnie aktualizuje last_login tylko przy formalnym logowaniu
    (signal user_logged_in). Przy dlugich sesjach (SESSION_COOKIE_AGE = 90 dni)
    pole przestaje odzwierciedlac rzeczywista aktywnosc - middleware to naprawia.

    is_active jest sprawdzane, bo Django nie uniewaznia sesji po deaktywacji
    konta - user z is_active=False moze nadal miec aktywna sesje, a jego
    aktualizacje odraczalyby usuniecie przez count_citizens.delete_inactive_users().
    """
    THROTTLE_SECONDS = 300

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_active:
            try:
                cache_key = f'last_seen:{request.user.pk}'
                # cache.add jest atomic - chroni przed race condition gdy dwa
                # rownolegle requesty tego samego usera trafia w pusty klucz.
                if cache.add(cache_key, True, self.THROTTLE_SECONDS):
                    User.objects.filter(pk=request.user.pk).update(last_login=timezone.now())
            except Exception:
                pass
        return self.get_response(request)
