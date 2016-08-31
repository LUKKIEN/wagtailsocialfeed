import logging

from django.core.cache import cache

from wagtailsocialfeed.utils.conf import get_socialfeed_setting

logger = logging.getLogger('wagtailsocialfeed')


class FeedError(Exception):
    pass


class AbstractFeed(object):
    def get_feed(self, config, *args, **kwargs):
        cls_name = self.__class__.__name__
        cache_key = 'socialfeed:{}:data:{}'.format(cls_name, config.id)

        data = cache.get(cache_key, [])
        if data:
            logger.debug("Getting data from cache ({})".format(cache_key))
        else:
            logger.debug("Fetching data online")
            data = self.fetch_online(config=config, *args, **kwargs)
            logger.debug("Storing data in cache ({})".format(cache_key))
            cache.set(cache_key, data,
                      get_socialfeed_setting('CACHE_DURATION'))
        return data

    def fetch_online(self, *args, **kwargs):
        raise NotImplementedError(
            "fetch_online() is not implemented yet by {}".format(
                self.__class__.__name__))
