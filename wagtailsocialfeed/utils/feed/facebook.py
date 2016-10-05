from dateutil import parser as dateparser
from django.core.exceptions import ImproperlyConfigured
from facepy import GraphAPI, FacebookError

from wagtailsocialfeed.utils.conf import get_socialfeed_setting

from . import AbstractFeed, AbstractFeedQuery, FeedItem
from enum import Enum


class PostType(Enum):
    status = 'status'
    photo = 'photo'
    link = 'link'
    video = 'video'
    offer = 'offer'
    event = 'event'

    def get_text_from(self, raw):
        """Get the display text from the raw data.

        Each post/object type has its different kind of data
        and so the text has to be distilled in different ways
        accoring to the object type.

        :param raw: the raw data
        """
        def _try_defaults():
            if 'message' in raw:
                return raw['message']
            return raw.get('story', '')

        if self is PostType.status:
            # Status
            return _try_defaults()

        if self is PostType.photo:
            # Photo
            if 'description' in raw:
                return raw['description']
            return _try_defaults()

        if self is PostType.link:
            # Link
            link = raw['link']
            if 'message' in raw:
                text = raw['message']
                if link not in text:
                    text += " " + link
                return text
            return raw['link']

        return _try_defaults()

        # if self is PostType.video:
        #     # implement
        #     pass
        # elif self is PostType.offer:
        #     # implement
        #     pass
        # elif self is PostType.event:
        #     # implement
        #     pass


class FacebookFeedItem(FeedItem):
    """Implements facebook-specific behaviour."""

    @classmethod
    def from_raw(cls, raw):
        item_type = PostType(raw['type'])
        text = ""

        if 'message' in raw:
            text = raw['message']
        elif 'story' in raw:
            text = raw['story']

        text = item_type.get_text_from(raw)

        image = {}

        if 'created_time' in raw:
            date = dateparser.parse(raw.get('created_time'))

        if 'picture' in raw:
            image = {
                'thumb': {'url': raw['picture']},
                # 'small': raw['images']['low_resolution'],
                # 'medium': raw['images']['standard_resolution'],
                # 'largel': None,
            }
        return cls(
            id=raw['id'],
            type='facebook',
            text=text,
            image_dict=image,
            posted=date,
            original_data=raw,
        )


class FacebookFeedQuery(AbstractFeedQuery):
    def __init__(self, username, query_string):
        super(FacebookFeedQuery, self).__init__(username, query_string)
        settings = get_socialfeed_setting('CONFIG').get('facebook', None)

        if not settings:
            raise ImproperlyConfigured(
                "No facebook configuration defined in the settings. "
                "Make sure you define WAGTAIL_SOCIALFEED_CONFIG in your "
                "settings with at least a 'facebook' entry.")

        graph = GraphAPI("{}|{}".format(settings['CLIENT_ID'], settings['CLIENT_SECRET']))
        self.paginator = graph.get('{}/posts'.format(self.username), page=True)

    def _search(self, item):
        """Very basic search function"""
        all_strings = " ".join([item.get('message', ''),
                                item.get('story', ''),
                                item.get('description', '')])
        return self.query_string.lower() in all_strings.lower()

    def __call__(self):
        raw = next(self.paginator)
        data = raw['data']
        oldest_post = None
        if data:
            oldest_post = data[-1]
            if self.query_string:
                data = list(filter(self._search, data))
        return data, oldest_post


class FacebookFeed(AbstractFeed):
    item_cls = FacebookFeedItem
    query_cls = FacebookFeedQuery

    def get_post_date(self, item):
        return dateparser.parse(item.get('created_time'))

    def fetch_older_items(self, query, oldest_post):
        return query()
