from __future__ import unicode_literals

import json
import logging

from django.core.cache import cache
from django.utils import six

from wagtailsocialfeed.utils.conf import get_socialfeed_setting

logger = logging.getLogger('wagtailsocialfeed')


def date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:  # pragma: no cover
        raise TypeError


class FeedError(Exception):
    pass


class FeedItem(object):
    def __init__(self, id, text, posted, image_dict, *args, **kwargs):
        self.id = six.text_type(id)  # Ensure it's a string
        self.text = text
        self.posted = posted
        self.image_dict = image_dict

    @property
    def image(self):
        """
        Convenience property to be used in templates.

        Can be used in templates as such::

            item.image.small.url
        """
        return self.image_dict

    def serialize(self):
        return json.dumps(vars(self), default=date_handler)

    @classmethod
    def from_moderated(cls, moderated):
        """Create an `FeedItem` object from a `ModeratedItem`"""
        source = json.loads(moderated.content)

        # We could convert source['posted'] to a proper DateTime
        # object but why bother when it is saved in
        # moderated.posted as well
        source['posted'] = moderated.posted
        return cls(**source)


class AbstractFeed(object):
    """
    All feed implementations should subclass this class.

    This base class provides caching functionality.
    The subclass needs to take care of actually fetching the feed from the
    online source and converting them to `FeedItem`s.
    """

    def get_items(self, config, limit=0):
        """
        Return a list of `FeedItem`s and handle caching.

        :param config: `SocialFeedConfiguration` to use
        :param limit: limit the output. Use 0 or None for no limit (default=0)

        """
        cls_name = self.__class__.__name__
        cache_key = 'socialfeed:{}:data:{}'.format(cls_name, config.id)

        data = cache.get(cache_key, [])
        if data:
            logger.debug("Getting data from cache ({})".format(cache_key))
        else:
            logger.debug("Fetching data online")
            data_raw = self.fetch_online(config=config, limit=limit)
            data = list(map(self._convert_raw_item, data_raw))

            logger.debug("Storing data in cache ({})".format(cache_key))
            cache.set(cache_key, data,
                      get_socialfeed_setting('CACHE_DURATION'))

        if limit:
            return data[:limit]
        return data

    def _convert_raw_item(self, raw):
        item = self.to_feed_item(raw)
        assert isinstance(item, FeedItem)
        return item

    def to_feed_item(self, raw):
        raise NotImplementedError(
            "to_feed_item() is not implemented yet by {}".format(
                self.__class__.__name__))

    def fetch_online(self, config, limit):
        raise NotImplementedError(
            "fetch_online() is not implemented yet by {}".format(
                self.__class__.__name__))
