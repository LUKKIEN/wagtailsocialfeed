import datetime

import requests
from django.utils import timezone

from . import AbstractFeed, FeedError


def prepare_item(item):
    date = None
    image = {}

    if 'created_time' in item:
        timestamp = None
        try:
            timestamp = float(item['created_time'])
        except ValueError:
            pass

        if timestamp:
            date = timezone.make_aware(
                datetime.datetime.fromtimestamp(timestamp),
                timezone=timezone.utc)

    if 'images' in item:
        image = {
            'thumb': item['images']['thumbnail'],
            'small': item['images']['low_resolution'],
            'medium': item['images']['standard_resolution'],
            'largel': None,
        }

    return {
        'id': item['id'],
        'text': item['caption']['text'],
        'image': image,
        'date': date,
        # 'instagram': item
        'type': 'instagram'
    }


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

            return list(map(prepare_item, items))

        raise FeedError(resp.reason)
