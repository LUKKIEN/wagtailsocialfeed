from __future__ import unicode_literals

from .feed.factory import FeedFactory


def get_feed_items(feedconfig, limit=0):
    """Return the items of a specific feed.

    :param feedconfig: the `SocialFeedConfiguration` to be used
    :param limit: limit the amount of items returned
    """
    if feedconfig.moderated:
        qs = feedconfig.moderated_items.all()
        if limit:
            return qs[:limit]
        return qs

    stream = FeedFactory.create(feedconfig.source)
    return stream.get_items(config=feedconfig, limit=limit)


def get_feed_items_mix(feedconfigs, limit=0):
    """Return the items of all the feeds combined.

    :param feedconfigs: a list of `SocialFeedConfiguration` objects
    :param limit: limit the result set
    """
    items = []
    for config in feedconfigs:
        items.extend(get_feed_items(config))

    # Make sure the date-order is correct
    items = sorted(items, key=lambda x: x.posted, reverse=True)
    if limit:
        return items[:limit]
    return items
