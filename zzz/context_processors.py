import logging

from django.conf import settings
from django.http import HttpRequest

from board.models import Post

log = logging.getLogger(__name__)


def footer(request: HttpRequest):
    footer = Post.objects.filter(title__iexact='Footer').order_by('-updated').first()
    return {
        'footer': footer
    }


def site_description(request):
    return {
        'site_description': settings.SITE_DESCRIPTION,
        'app_version': settings.APP_VERSION,
    }
