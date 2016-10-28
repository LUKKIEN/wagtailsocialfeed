import logging

from dateutil import parser as dateparser
from django.core.exceptions import ImproperlyConfigured
from twython import Twython
from wagtailsocialfeed.utils.conf import get_socialfeed_setting

from . import AbstractFeed, AbstractFeedQuery, FeedItem

logger = logging.getLogger('wagtailsocialfeed')

settings = get_socialfeed_setting('CONFIG').get('twitter', None)
if not settings:
    raise ImproperlyConfigured(
        "No twitter configuration defined in the settings. "
        "Make sure you define WAGTAIL_SOCIALFEED_CONFIG in your "
        "settings with at least a 'twitter' entry.")


class TwitterFeedItem(FeedItem):
    @classmethod
    def get_post_date(cls, raw):
        # Use the dateutil parser because on some platforms
        # python's own strptime doesn't support the %z directive.
        # Format: '%a %b %d %H:%M:%S %z %Y'
        return dateparser.parse(raw.get('created_at'))

    @classmethod
    def from_raw(cls, raw):
        image = None
        extended = raw.get('extended_entities', None)
        if extended:
            image = process_images(extended.get('media', None))
        date = cls.get_post_date(raw)
        return cls(
            id=raw['id'],
            type='twitter',
            text=raw['text'],
            image_dict=image,
            posted=date,
            original_data=raw
        )


def process_images(media_dict):
    images = {}
    if not media_dict:
        return images
    base_url = media_dict[0]['media_url_https']
    sizes = media_dict[0]['sizes']

    for size in sizes:
        images[size] = {
            'url': '{0}:{1}'.format(base_url, size),
            'width': sizes[size]['w'],
            'height': sizes[size]['h'],
        }
    return images


class TwitterFeedQuery(AbstractFeedQuery):
    def __init__(self, username, query_string):
        super(TwitterFeedQuery, self).__init__(username, query_string)

        self.twitter = Twython(settings['CONSUMER_KEY'],
                               settings['CONSUMER_SECRET'],
                               settings['ACCESS_TOKEN_KEY'],
                               settings['ACCESS_TOKEN_SECRET'])

    def _get_load_kwargs(self, oldest_post):
        # Trick from twitter API doc to exclude the oldest post from
        # the next result-set
        return {'max_id': self.oldest_post['id'] - 1}

    def _search(self, raw_item):
        """Very basic search function"""
        return self.query_string.lower() in raw_item['text'].lower()

    def _load(self, max_id=None):
        """Return the raw data fetched from twitter."""
        options = settings.get('OPTIONS', {})
        return self.twitter.get_user_timeline(
            screen_name=self.username,
            trim_user=options.get('trim_user', True),
            contributor_details=options.get('contributor_details', False),
            include_rts=options.get('include_rts', False),
            max_id=max_id)


class TwitterFeed(AbstractFeed):
    item_cls = TwitterFeedItem
    query_cls = TwitterFeedQuery
