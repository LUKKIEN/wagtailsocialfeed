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
    def get_post_date(cls, raw):
        if 'created_time' in raw:
            return dateparser.parse(raw.get('created_time'))
        return None

    @classmethod
    def from_raw(cls, raw):
        item_type = PostType(raw['type'])
        image = {}
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
            text=item_type.get_text_from(raw),
            image_dict=image,
            posted=cls.get_post_date(raw),
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
        self._paginator = graph.get('{}/posts'.format(self.username), page=True)

    def _search(self, raw_item):
        """Very basic search function"""
        all_strings = " ".join([raw_item.get('message', ''),
                                raw_item.get('story', ''),
                                raw_item.get('description', '')])
        return self.query_string.lower() in all_strings.lower()

    def _load(self):
        raw = next(self._paginator)
        return raw['data']


class FacebookFeed(AbstractFeed):
    item_cls = FacebookFeedItem
    query_cls = FacebookFeedQuery
