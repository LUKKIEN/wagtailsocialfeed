import datetime
import logging

import requests
from django.utils import timezone

from . import AbstractFeed, FeedError, FeedItem

logger = logging.getLogger('wagtailsocialfeed')


def _raw_timestamp_to_date(ts):
    timestamp = None
    try:
        timestamp = float(ts)
    except ValueError:
        return None

    return timezone.make_aware(
        datetime.datetime.fromtimestamp(timestamp), timezone=timezone.utc)


class InstagramFeedItem(FeedItem):
    """Implements instagram-specific behaviour"""

    @classmethod
    def from_raw(cls, raw):
        date = None
        image = {}

        if 'created_time' in raw:
            date = _raw_timestamp_to_date(raw['created_time'])

        if 'images' in raw:
            image = {
                'thumb': raw['images']['thumbnail'],
                'small': raw['images']['low_resolution'],
                'medium': raw['images']['standard_resolution'],
                'largel': None,
            }

        return cls(
            id=raw['id'],
            text=raw['caption']['text'],
            image_dict=image,
            posted=date,
        )


class InstagramFeed(AbstractFeed):
    def fetch_online(self, config, limit=None, query_string=None):
        username = config.username

        def _search(tweet):
            """Very basic search function"""
            return query_string.lower() in tweet['caption']['text'].lower()

        def _fetch(max_id=None):
            url = "https://www.instagram.com/{}/media/".format(username)
            if max_id:
                url += "?max_id={}".format(max_id)

            resp = requests.get(url)
            if resp.status_code == 200:
                try:
                    raw = resp.json()['items']
                except ValueError as e:
                    raise FeedError(e)
                except KeyError as e:
                    raise FeedError("No items could be found in the response")

                if not raw:
                    return raw, None

                oldest_post = raw[-1]
                if query_string:
                    raw = list(filter(_search, raw))
                return raw, oldest_post
            raise FeedError(resp.reason)

        raw, oldest_post = _fetch()

        if query_string:
            # If we have a query_string, we should fetch the users timeline a
            # couple of times to dig a bit into the history.
            while oldest_post:
                # Trick from twitter API doc to exclude the oldest post from
                # the next result-set
                oldest_post_date = _raw_timestamp_to_date(
                    oldest_post['created_time'])
                if not self.more_history_allowed(oldest_post_date):
                    break

                _raw, _post = _fetch(max_id=oldest_post['id'])
                if _post and _post['id'] == oldest_post['id']:
                    logger.warning("Trying to fetch older tweets but received "
                                   "same result set. Breaking the loop.")
                    break
                oldest_post = _post
                raw += _raw

        return raw

    def to_feed_item(self, raw):
        return InstagramFeedItem.from_raw(raw)
