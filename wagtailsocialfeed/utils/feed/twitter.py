import logging
import json

from dateutil import parser as dateparser
from django.core.exceptions import ImproperlyConfigured
from twython import Twython

from wagtailsocialfeed.utils.conf import get_socialfeed_setting

from . import AbstractFeed, FeedItem

logger = logging.getLogger('wagtailsocialfeed')


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


class TwitterFeed(AbstractFeed):
    def __init__(self, *args, **kwargs):
        super(TwitterFeed, self).__init__(*args, **kwargs)

        self.settings = get_socialfeed_setting('CONFIG').get('twitter', None)
        if not self.settings:
            raise ImproperlyConfigured(
                "No twitter configuration defined in the settings. "
                "Make sure you define WAGTAIL_SOCIALFEED_CONFIG in your "
                "settings with at least a 'twitter' entry.")

        self.twitter = Twython(self.settings['CONSUMER_KEY'],
                               self.settings['CONSUMER_SECRET'],
                               self.settings['ACCESS_TOKEN_KEY'],
                               self.settings['ACCESS_TOKEN_SECRET'])

    def fetch_online(self, config, limit=None, query_string=None, max_id=None):
        username = config.username

        def _search(tweet):
            """Very basic search function"""
            return query_string.lower() in tweet['text'].lower()

        self.iteration = 0

        def _fetch(max_id=None):
            """
            Return the raw data fetched from twitter and the oldest post in the
            result set.

            We return the oldest post as well because the raw data might be
            filtered based on the query_string, but we still need the oldest
            post to check the date to determine wether we should stop our
            search or continue
            """
            raw = self.twitter.get_user_timeline(
                screen_name=username,
                trim_user=True,
                contributor_details=False,
                include_rts=False,
                max_id=max_id)

            if not raw:
                return raw, None

            oldest_post = raw[-1]
            if query_string:
                raw = list(filter(_search, raw))
            return raw, oldest_post

        raw, oldest_post = _fetch()

        if query_string:
            # If we have a query_string, we should fetch the users timeline a
            # couple of times to dig a bit into the history.
            while oldest_post:
                # Trick from twitter API doc to exclude the oldest post from
                # the next result-set
                oldest_post_date = dateparser.parse(oldest_post.get(
                    'created_at'))
                if not self.more_history_allowed(oldest_post_date):
                    break

                max_id = oldest_post['id'] - 1
                _raw, _post = _fetch(max_id=max_id)
                if _post and _post['id'] == oldest_post['id']:
                    logger.warning("Trying to fetch older tweets but received "
                                   "same result set. Breaking the loop.")
                    break
                oldest_post = _post
                raw += _raw

        return raw

    def to_feed_item(self, raw):
        return TwitterFeedItem.from_raw(raw)
