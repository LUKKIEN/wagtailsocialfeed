import datetime
import logging

import requests
from django.utils import timezone

from . import AbstractFeed, AbstractFeedQuery, FeedError, FeedItem

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


class InstagramFeedQuery(AbstractFeedQuery):
    def _search(self, item):
        """Very basic search function"""
        return self.query_string.lower() in item['caption']['text'].lower()

    def __call__(self, max_id=None):
        url = "https://www.instagram.com/{}/media/".format(self.username)
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
            if self.query_string:
                raw = list(filter(self._search, raw))
            return raw, oldest_post
        raise FeedError(resp.reason)


class InstagramFeed(AbstractFeed):
    item_cls = InstagramFeedItem
    query_cls = InstagramFeedQuery

    def get_post_date(self, item):
        return _raw_timestamp_to_date(item['created_time'])

    def fetch_older_items(self, query, oldest_post):
        return query(max_id=oldest_post['id'])
