from __future__ import unicode_literals

from .feed.factory import FeedFactory


def get_feed_items(feedconfig, limit=0):
    if feedconfig.moderated:
        qs = feedconfig.moderated_items.all()
        if limit:
            return qs[:limit]
        return qs

    stream = FeedFactory.create(feedconfig.source)
    return stream.get_items(config=feedconfig, limit=limit)
