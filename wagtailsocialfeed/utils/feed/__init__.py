from __future__ import unicode_literals

import json
import logging
import datetime
from dateutil.tz import tzutc

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
    def __init__(self, id, type, text, posted, image_dict, *args, **kwargs):
        self.id = six.text_type(id)  # Ensure it's a string
        self.type = type
        self.text = text
        self.posted = posted
        self.image_dict = image_dict
        self.original_data = kwargs.get('original_data', {})

    def __repr__(self):
        return "{} ({} posted {})".format(self.__class__.__name__, self.id, self.posted)

    @classmethod
    def get_post_date(cls, raw):
        raise NotImplementedError

    @property
    def image(self):
        """
        Convenience property to be used in templates.

        Can be used in templates as such::

            item.image.small.url
        """
        return self.image_dict

    def __getattribute__(self, name):
        """
        Look for attributes in both the `FeedItem` as well as the original data.

        Return an `AttributeError` when the attribute can't be found in either
        of the two sources
        """
        try:
            return object.__getattribute__(self, name)
        except AttributeError as e:
            original_data = object.__getattribute__(self, 'original_data')
            if name in original_data:
                return original_data[name]
            raise e

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
        source['type'] = moderated.type
        item = cls(**source)
        return item


class AbstractFeedQuery(object):
    """
    Query class to facilitate the actual fetch on the feed source.

    Needs to have a source-specific implementation.
    Once implemented for, say, twitter, it can be used as follows:

        query = TwitterFeedQuery()
        tweets = query()

    or, in order to fetch some older tweets:

        older_tweets = query(max_id=<some id>)
    """
    def __init__(self, username, query_string):
        self.username = username
        self.query_string = query_string

        # Things needed for the paginator
        self.exhausted = False
        self.oldest_post = None

    def get_paginator(self):
        while not self.exhausted:
            kwargs, result = {}, []
            if self.oldest_post:
                kwargs = self._get_load_kwargs(self.oldest_post)
            try:
                result, self.oldest_post = self.__load(**kwargs)
            finally:
                if not result:
                    self.exhausted = True
            yield result, self.oldest_post

    def _get_load_kwargs(self, oldest_post):
        """Get the kwargs needed to `self._load()` to get the correct results."""
        return {}

    def __load(self, **kwargs):
        """Private method to load the raw results and the oldest post in the
        result set.

        We return the oldest post as well because the raw data might be
        filtered based on the query_string, but we still need the oldest
        post to check the date to determine wether we should stop our
        search or continue

        It will call the protected `_load()` method, perform
        a search when needed and store the oldest post.
        """
        raw = self._load(**kwargs)

        if not raw:
            return raw, None

        oldest_post = raw[-1]
        if self.query_string:
            raw = list(filter(self._search, raw))
        return raw, oldest_post

    def _search(self, raw_item):
        raise NotImplementedError("_search() needs to be implemented by the subclas")

    def _load(self, **kwargs):
        raise NotImplementedError("_load() needs to be implemented by the subclass")


class AbstractFeed(object):
    """
    All feed implementations should subclass this class.

    This base class provides caching functionality.
    The subclass needs to take care of actually fetching the feed from the
    online source and converting them to `FeedItem`s.
    """

    def get_items(self, config, limit=0, query_string=None, use_cache=True):
        """
        Return a list of `FeedItem`s and handle caching.

        :param config: `SocialFeedConfiguration` to use
        :param limit: limit the output. Use 0 or None for no limit (default=0)
        :param query_string: the search term to filter on (default=None)
        :param use_cache: utilize the cache store/retreive the results
            (default=True)
        """
        cls_name = self.__class__.__name__
        cache_key = 'socialfeed:{}:data:{}'.format(cls_name, config.id)

        if query_string:
            cache_key += ":q-{}".format(query_string)

        data = cache.get(cache_key, []) if use_cache else None
        if data:
            logger.debug("Getting data from cache ({})".format(cache_key))
        else:
            logger.debug("Fetching data online")

            data_raw = self._fetch_online(config=config, query_string=query_string)
            data = list(map(self._convert_raw_item, data_raw))

            if use_cache:
                logger.debug("Storing data in cache ({})".format(cache_key))
                cache.set(cache_key, data,
                          get_socialfeed_setting('CACHE_DURATION'))

        if limit:
            return data[:limit]
        return data

    def _more_history_allowed(self, oldest_date):
        """
        Determine if we should load more history.

        This is used when searching for specific posts
        using the `query_string` argument.

        :param oldest_date: date of the oldest post in the last set returned
        """
        now = datetime.datetime.now(tzutc())
        last_allowed = now - get_socialfeed_setting('SEARCH_MAX_HISTORY')
        return oldest_date > last_allowed

    def _fetch_online(self, config, query_string=None):
        """
        Fetch the data from the online source.

        By default it will query just one result-page from the online source.
        When a `query_string` is given, multiple pages can be retreived in order
        to increase the changes of returning a usefull result-set.
        The size of the history to be searched through is specified in `SEARCH_MAX_HISTORY`
        (see `_more_history_allowed` for the specific implementation).

        :param config: `SocialFeedConfiguration` to use
        :param query_string: the search term to filter on (default=None)
        """
        if not hasattr(self, 'query_cls'):
            raise NotImplementedError('query_cls needs to be defined')

        query = self.query_cls(config.username, query_string)
        paginator = query.get_paginator()
        raw, oldest_post = next(paginator)
        if query_string:
            # If we have a query_string, we should fetch the users timeline a
            # couple of times to dig a bit into the history.
            for _raw, _oldest_post in paginator:
                if not _raw:
                    break

                oldest_post_date = self._convert_raw_item(oldest_post).posted
                if not self._more_history_allowed(oldest_post_date):
                    break

                if _oldest_post['id'] == oldest_post['id']:
                    logger.warning("Trying to fetch older items but received "
                                   "same result set. Breaking the loop.")
                    break
                oldest_post = _oldest_post
                raw += _raw

        return raw

    def _convert_raw_item(self, raw):
        """Convert a raw data-dict into a FeedItem subclass."""
        item = self.item_cls.from_raw(raw)
        assert isinstance(item, FeedItem)
        return item
