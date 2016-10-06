import datetime
import logging

import requests
from django.utils import timezone

from . import AbstractFeed, AbstractFeedQuery, FeedError, FeedItem

logger = logging.getLogger('wagtailsocialfeed')


class InstagramFeedItem(FeedItem):
    """Implements instagram-specific behaviour"""

    @classmethod
    def get_post_date(cls, raw):
        if 'created_time' in raw:
            timestamp = None
            try:
                timestamp = float(raw['created_time'])
            except ValueError:
                return None

            return timezone.make_aware(
                datetime.datetime.fromtimestamp(timestamp), timezone=timezone.utc)

        return None

    @classmethod
    def from_raw(cls, raw):
        image = {}

        if 'images' in raw:
            image = {
                'thumb': raw['images']['thumbnail'],
                'small': raw['images']['low_resolution'],
                'medium': raw['images']['standard_resolution'],
                'large': None,
            }

        return cls(
            id=raw['id'],
            type='instagram',
            text=raw['caption']['text'],
            image_dict=image,
            posted=cls.get_post_date(raw),
            original_data=raw,
        )


class InstagramFeedQuery(AbstractFeedQuery):
    def _get_load_kwargs(self, oldest_post):
        # Trick from twitter API doc to exclude the oldest post from
        # the next result-set
        return {'max_id': self.oldest_post['id']}

    def _search(self, raw_item):
        """Very basic search function"""
        return self.query_string.lower() in raw_item['caption']['text'].lower()

    def _load(self, max_id=None):
        url = "https://www.instagram.com/{}/media/".format(self.username)
        if max_id:
            url += "?max_id={}".format(max_id)

        resp = requests.get(url)
        if resp.status_code == 200:
            try:
                return resp.json()['items']
            except ValueError as e:
                raise FeedError(e)
            except KeyError as e:
                raise FeedError("No items could be found in the response")
        raise FeedError(resp.reason)


class InstagramFeed(AbstractFeed):
    item_cls = InstagramFeedItem
    query_cls = InstagramFeedQuery
