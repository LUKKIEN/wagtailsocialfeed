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
        if 'date' in raw:
            timestamp = None
            try:
                timestamp = float(raw['date'])
            except ValueError:
                return None
            return timezone.make_aware(
                datetime.datetime.fromtimestamp(timestamp), timezone=timezone.utc)

        return None

    @classmethod
    def from_raw(cls, raw):
        image = {}
        caption = None
        if 'display_src' in raw:
            image = {
                'thumb': raw['thumbnail_resources'][1],
                'small': raw['thumbnail_resources'][2],
                'medium': raw['thumbnail_resources'][3],
                'large': raw['thumbnail_resources'][4],
                'original_link': "https://www.instagram.com/p/" + raw['code']
            }

        if 'caption' in raw:
            caption = raw['caption']

        return cls(
            id=raw['id'],
            type='instagram',
            text=caption,
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
        return self.query_string.lower() in raw_item

    def _load(self, max_id=None):
        url = "https://www.instagram.com/{}/?__a=1".format(self.username)
        if max_id:
            url += "?max_id={}".format(max_id)
        resp = requests.get(url)
        if resp.status_code == 200:
            try:
                return resp.json()['user']['media']['nodes']
            except ValueError as e:
                raise FeedError(e)
            except KeyError as e:
                raise FeedError("No items could be found in the response")
        raise FeedError(resp.reason)


class InstagramFeed(AbstractFeed):
    item_cls = InstagramFeedItem
    query_cls = InstagramFeedQuery
