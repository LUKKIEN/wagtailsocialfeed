from .twitter import TwitterFeed, TwitterFeedItem
from .instagram import InstagramFeed, InstagramFeedItem
from .facebook import FacebookFeed, FacebookFeedItem

from collections import namedtuple

FeedClasses = namedtuple('FeedClasses', ['feed', 'item'])

FEED_CONFIG = {
    'twitter': FeedClasses(TwitterFeed, TwitterFeedItem),
    'instagram': FeedClasses(InstagramFeed, InstagramFeedItem),
    'facebook': FeedClasses(FacebookFeed, FacebookFeedItem)
}


class FeedFactory(object):
    @classmethod
    def create(cls, source):
        try:
            return FEED_CONFIG[source].feed()
        except KeyError:
            raise NotImplementedError(
                "Feed class for type '{}' not available".format(source))


class FeedItemFactory(object):
    @classmethod
    def get_class(cls, source):
        try:
            return FEED_CONFIG[source].item
        except KeyError:
            raise NotImplementedError(
                "FeedItem class for type '{}' not available".format(source))
