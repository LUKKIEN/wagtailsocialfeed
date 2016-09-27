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
    def from_raw(cls, raw):
        image = None
        extended = raw.get('extended_entities', None)
        if extended:
            image = process_images(extended.get('media', None))

        # Use the dateutil parser because on some platforms
        # python's own strptime doesn't support the %z directive.
        # Format: '%a %b %d %H:%M:%S %z %Y'
        date = dateparser.parse(raw.get('created_at'))
        return cls(
            id=raw['id'],
            text=raw['text'],
            image_dict=image,
            posted=date
        )


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


class TwitterFeedQuery(AbstractFeedQuery):
    def __init__(self, username, query_string):
        super(TwitterFeedQuery, self).__init__(username, query_string)

        self.twitter = Twython(settings['CONSUMER_KEY'],
                               settings['CONSUMER_SECRET'],
                               settings['ACCESS_TOKEN_KEY'],
                               settings['ACCESS_TOKEN_SECRET'])

    def _search(self, tweet):
        """Very basic search function"""
        return self.query_string.lower() in tweet['text'].lower()

    def __call__(self, max_id=None):
        """
        Return the raw data fetched from twitter and the oldest post in the
        result set.

        We return the oldest post as well because the raw data might be
        filtered based on the query_string, but we still need the oldest
        post to check the date to determine wether we should stop our
        search or continue
        """
        raw = self.twitter.get_user_timeline(
            screen_name=self.username,
            trim_user=True,
            contributor_details=False,
            include_rts=False,
            max_id=max_id)

        if not raw:
            return raw, None

        oldest_post = raw[-1]
        if self.query_string:
            raw = list(filter(self._search, raw))
        return raw, oldest_post


class TwitterFeed(AbstractFeed):
    item_cls = TwitterFeedItem
    query_cls = TwitterFeedQuery

    def get_post_date(self, item):
        return dateparser.parse(item.get('created_at'))

    def fetch_older_items(self, query, oldest_post):
        # Trick from twitter API doc to exclude the oldest post from
        # the next result-set
        max_id = oldest_post['id'] - 1
        return query(max_id=max_id)
