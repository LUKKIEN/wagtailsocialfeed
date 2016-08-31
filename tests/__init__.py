from __future__ import unicode_literals

import json
import re
from functools import wraps

import responses


def date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError


def _twitter(modifier):
    with open('tests/fixtures/tweets.json', 'r') as feed_file:
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
    return feed


def feed_response(source, modifier=None):
    def decorator(func):
        @wraps(func)
        @responses.activate
        def func_wrapper(obj, *args, **kwargs):
            if source == 'twitter':
                feed = _twitter(modifier)
            elif source == 'instagram':
                feed = _instagram(modifier)
            return func(obj, feed, *args, **kwargs)
        return func_wrapper
    return decorator
