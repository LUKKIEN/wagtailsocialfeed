from __future__ import unicode_literals

import json
import re
from functools import wraps

import responses


def _twitter(modifier):
    with open('tests/fixtures/twitter.json', 'r') as feed_file:
        feed = json.loads("".join(feed_file.readlines()))
    if modifier:
        feed = modifier(feed)
    responses.add(responses.GET,
                  re.compile('https?://api.twitter.com/.*'),
                  json=feed, status=200)
    return feed


def _instagram(modifier):
    with open('tests/fixtures/instagram.json', 'r') as feed_file:
        feed = json.loads("".join(feed_file.readlines()))
    if modifier:
        feed = modifier(feed)
    responses.add(responses.GET,
                  re.compile('https?://www.instagram.com/.*'),
                  json=feed, status=200)
    try:
        return feed['items']
    except KeyError:
        return []


def feed_response(sources, modifier=None):
    def decorator(func):
        @wraps(func)
        @responses.activate
        def func_wrapper(obj, *args, **kwargs):
            source_list = sources
            feeds = []
            if type(sources) is not list:
                source_list = [sources]

            for source in source_list:
                if source == 'twitter':
                    feeds.append(_twitter(modifier))
                elif source == 'instagram':
                    feeds.append(_instagram(modifier))
            feeds.extend(args)
            return func(obj, *feeds, **kwargs)
        return func_wrapper
    return decorator
