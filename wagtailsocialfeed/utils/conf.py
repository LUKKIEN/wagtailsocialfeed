from __future__ import absolute_import, unicode_literals

from django.conf import settings
from datetime import timedelta

DEFAULTS = {
    'CONFIG': {},
    'CACHE_DURATION': 900,
    'SEARCH_MAX_HISTORY': timedelta(weeks=26)
}


def get_socialfeed_setting(name):
    return getattr(settings, 'WAGTAIL_SOCIALFEED_{}'.format(name),
                   DEFAULTS[name])
