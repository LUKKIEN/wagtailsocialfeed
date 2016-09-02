from __future__ import unicode_literals

import logging

from django.core.cache import cache

from wagtailsocialfeed.utils.conf import get_socialfeed_setting

logger = logging.getLogger('wagtailsocialfeed')


class FeedError(Exception):
    pass


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
            data = self.fetch_online(config=config, limit=limit)
            logger.debug("Storing data in cache ({})".format(cache_key))
            cache.set(cache_key, data,
                      get_socialfeed_setting('CACHE_DURATION'))

        if limit:
            return data[:limit]
        return data

    def fetch_online(self, config, limit):
        raise NotImplementedError(
            "fetch_online() is not implemented yet by {}".format(
                self.__class__.__name__))
