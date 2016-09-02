import datetime

import requests
from django.utils import timezone

from . import AbstractFeed, FeedError, FeedItem


class InstagramFeedItem(FeedItem):
    """Implements instagram-specific behaviour"""

    @classmethod
    def from_raw(cls, raw):
        date = None
        image = {}

        if 'created_time' in raw:
            timestamp = None
            try:
                timestamp = float(raw['created_time'])
            except ValueError:
                pass

            if timestamp:
                date = timezone.make_aware(
                    datetime.datetime.fromtimestamp(timestamp),
                    timezone=timezone.utc)

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
    def fetch_online(self, config, limit=None):
        username = config.username

        url = "https://www.instagram.com/{}/media/".format(username)
        resp = requests.get(url)
        if resp.status_code == 200:
            try:
                items = resp.json()['items']
            except ValueError as e:
                raise FeedError(e)
            except KeyError as e:
                raise FeedError("No items could be found in the response")
            return items

        raise FeedError(resp.reason)

    def to_feed_item(self, raw):
        return InstagramFeedItem.from_raw(raw)
