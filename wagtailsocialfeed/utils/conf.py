from __future__ import absolute_import, unicode_literals

from django.conf import settings

DEFAULTS = {
    'CONFIG': {},
    'CACHE_DURATION': 900,
}


def get_socialfeed_setting(name):
    return getattr(settings, 'WAGTAIL_SOCIALFEED_{}'.format(name),
                   DEFAULTS[name])
