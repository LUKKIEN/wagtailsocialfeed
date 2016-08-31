from dateutil import parser as dateparser
from django.core.exceptions import ImproperlyConfigured
from twython import Twython

from wagtailsocialfeed.utils.conf import get_socialfeed_setting

from . import AbstractFeed


def process_images(media_dict):
    images = {}
    if not media_dict:
        return images
    base_url = media_dict[0]['media_url_https']

    # TODO: see if we can provide the width and height attributes as well
    images['small'] = dict(url=base_url + ":small")
    images['thumb'] = dict(url=base_url + ":thumb")
    images['medium'] = dict(url=base_url + ":medium")
    images['large'] = dict(url=base_url + ":large")
    return images


def prepare_item(item):
    image = None
    extended = item.get('extended_entities', None)
    if extended:
        image = process_images(extended.get('media', None))

    item['image'] = image

    # Use the dateutil parser because on some platforms
    # python's own strptime doesn't support the %z directive.
    # Format: '%a %b %d %H:%M:%S %z %Y'
    item['date'] = dateparser.parse(item.get('created_at'))

    return item


class TwitterFeed(AbstractFeed):
    def __init__(self, *args, **kwargs):
        super(TwitterFeed, self).__init__(*args, **kwargs)

        self.settings = get_socialfeed_setting('CONFIG').get('twitter', None)
        if not self.settings:
            raise ImproperlyConfigured(
                "No twitter configuration defined in the settings. "
                "Make sure you define WAGTAIL_SOCIALFEED_CONFIG in your "
                "settings with at least a 'twitter' entry.")

    def fetch_online(self, config, limit=None):
        username = config.username
        twitter = Twython(self.settings['CONSUMER_KEY'],
                          self.settings['CONSUMER_SECRET'],
                          self.settings['ACCESS_TOKEN_KEY'],
                          self.settings['ACCESS_TOKEN_SECRET'])

        tweets = twitter.get_user_timeline(
            screen_name=username,
            trim_user=True,
            contributor_details=False,
            include_rts=False)
        return list(map(prepare_item, tweets))
