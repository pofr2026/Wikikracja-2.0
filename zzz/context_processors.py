import logging

from django.conf import settings
from django.http import HttpRequest

import zzz
from board.models import Post

log = logging.getLogger(__name__)


def footer(request: HttpRequest):
    footer = Post.get_system_post('footer')
    return {
        'footer': footer
    }


def site_description(request):
    return {
        'site_description': settings.SITE_DESCRIPTION,
        'app_version': zzz.__version__,
    }
