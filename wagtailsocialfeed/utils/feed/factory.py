from .twitter import TwitterFeed
from .instagram import InstagramFeed


class FeedFactory(object):
    @classmethod
    def create(cls, source):
        if source == 'twitter':
            return TwitterFeed()
        if source == 'instagram':
            return InstagramFeed()
        raise NotImplementedError(
            "Feed class for type '{}' not available".format(source))
