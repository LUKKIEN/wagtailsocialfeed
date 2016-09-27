import datetime
import json
import re

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

import responses
from wagtailsocialfeed.utils.feed import AbstractFeed, FeedError, FeedItem
from wagtailsocialfeed.utils.feed.factory import FeedFactory
from wagtailsocialfeed.utils.feed.instagram import InstagramFeed
from wagtailsocialfeed.utils.feed.twitter import TwitterFeed

from . import feed_response
from .factories import SocialFeedConfigurationFactory


class AbstractFeedTest(TestCase):
    def setUp(self):
        self.feedconfig = SocialFeedConfigurationFactory.create(
            source='abstract',
            username='someuser')
        self.feed = AbstractFeed()

    def test_get_items(self):
        with self.assertRaises(NotImplementedError):
            self.feed.get_items(self.feedconfig)


class FeedFactoryTest(TestCase):
    def test_create(self):
        self.assertIsInstance(FeedFactory.create('twitter'), TwitterFeed)
        self.assertIsInstance(FeedFactory.create('instagram'), InstagramFeed)
        with self.assertRaises(NotImplementedError):
            FeedFactory.create('ello')


class TwitterFeedTest(TestCase):
    def setUp(self):
        cache.clear()
        self.feedconfig = SocialFeedConfigurationFactory.create(
            source='twitter',
            username='wagtailcms')
        self.stream = FeedFactory.create('twitter')
        self.cache_key = 'socialfeed:{}:data:{}'.format(
            'TwitterFeed', self.feedconfig.id)

    @feed_response('twitter')
    def test_feed(self, feed):
        self.assertIsNone(cache.get(self.cache_key))
        stream = self.stream.get_items(config=self.feedconfig)

        self.assertIsNotNone(cache.get(self.cache_key))
        self.assertEqual(len(stream), 17)
        for item in stream:
            assert isinstance(item, FeedItem)
        self.assertEqual(
            stream[0].posted,
            datetime.datetime(2016, 9, 23, 8, 28, 16, tzinfo=timezone.utc))
        self.assertIsNone(stream[0].image_dict)

        self.assertIsNotNone(stream[-1].image_dict)
        base_url = 'https://pbs.twimg.com/media/CnpYVx0UkAEdCpU.jpg'

        self.assertEqual(stream[-1].image_dict['small']['url'],
                         base_url + ":small")
        self.assertEqual(stream[-1].image_dict['thumb']['url'],
                         base_url + ":thumb")
        self.assertEqual(stream[-1].image_dict['medium']['url'],
                         base_url + ":medium")
        self.assertEqual(stream[-1].image_dict['large']['url'],
                         base_url + ":large")

    @responses.activate
    def test_search(self):
        with open('tests/fixtures/twitter.json', 'r') as feed_file:
            page1 = json.loads("".join(feed_file.readlines()))
        with open('tests/fixtures/twitter.2.json', 'r') as feed_file:
            page2 = json.loads("".join(feed_file.readlines()))

        responses.add(responses.GET,
                      re.compile('(?!.*max_id=\d*)https?://api.twitter.com.*'),
                      json=page1, status=200)

        responses.add(responses.GET,
                      re.compile('(?=.*max_id=\d*)https?://api.twitter.com.*'),
                      json=page2, status=200)

        q = "release"
        cache_key = "{}:q-{}".format(self.cache_key, q)

        self.assertIsNone(cache.get(cache_key))
        stream = self.stream.get_items(config=self.feedconfig,
                                       query_string=q)
        self.assertIsNotNone(cache.get(cache_key))
        self.assertEqual(len(stream), 2)
        for s in stream:
            self.assertIn('release', s.text)

    @feed_response('twitter')
    def test_without_cache(self, feed):
        self.assertIsNone(cache.get(self.cache_key))
        stream = self.stream.get_items(config=self.feedconfig,
                                       use_cache=False)
        self.assertIsNone(cache.get(self.cache_key))
        self.assertEqual(len(stream), 17)


def _tamper_date(resp):
    """
    Alter instagram response so that it returns
    some unexpected data
    """
    resp['items'][0]['created_time'] = "not_a_timestamp"
    return resp


def _remove_items(resp):
    return {"message": 'Instagram did some drastic changes!'}


class InstagramFeedTest(TestCase):
    def setUp(self):
        cache.clear()
        self.feedconfig = SocialFeedConfigurationFactory.create(
            source='instagram')
        self.stream = FeedFactory.create('instagram')
        self.cache_key = 'socialfeed:{}:data:{}'.format(
            'InstagramFeed', self.feedconfig.id)

    @feed_response('instagram')
    def test_feed(self, feed):
        self.assertIsNone(cache.get(self.cache_key))
        stream = self.stream.get_items(config=self.feedconfig)

        self.assertIsNotNone(cache.get(self.cache_key))
        self.assertEqual(len(stream), 20)

        for item in stream:
            assert isinstance(item, FeedItem)
        self.assertEqual(
            stream[0].posted,
            datetime.datetime(2016, 8, 17, 4, 31, 47, tzinfo=timezone.utc))

        self.assertEqual(stream[0].image_dict['small']['url'],
                         "https://scontent-frt3-1.cdninstagram.com/t51.2885-15/s320x320/e35/14026774_1163660323707262_1160471917_n.jpg?ig_cache_key=MTMxODUzMDUxMDQyNzYzNjA2Mg%3D%3D.2.l" # NOQA
                         )
        self.assertEqual(stream[0].image_dict['thumb']['url'],
                         "https://scontent-frt3-1.cdninstagram.com/t51.2885-15/s150x150/e35/c136.0.448.448/14032893_1190601567673451_1118658827_n.jpg?ig_cache_key=MTMxODUzMDUxMDQyNzYzNjA2Mg%3D%3D.2.c" # NOQA
                         )
        self.assertEqual(stream[0].image_dict['medium']['url'],
                         "https://scontent-frt3-1.cdninstagram.com/t51.2885-15/s640x640/sh0.08/e35/14026774_1163660323707262_1160471917_n.jpg?ig_cache_key=MTMxODUzMDUxMDQyNzYzNjA2Mg%3D%3D.2.l" # NOQA
                         )

    @responses.activate
    def test_search(self):
        with open('tests/fixtures/instagram.json', 'r') as feed_file:
            page1 = json.loads("".join(feed_file.readlines()))
        with open('tests/fixtures/instagram.2.json', 'r') as feed_file:
            page2 = json.loads("".join(feed_file.readlines()))

        responses.add(
            responses.GET,
            re.compile('(?!.*max_id=\d*)https?://www.instagram.com.*'),
            json=page1, status=200)

        responses.add(
            responses.GET,
            re.compile('(?=.*max_id=\d*)https?://www.instagram.com.*'),
            json=page2, status=200)

        q = "programming"
        cache_key = "{}:q-{}".format(self.cache_key, q)

        self.assertIsNone(cache.get(cache_key))
        stream = self.stream.get_items(config=self.feedconfig,
                                       query_string=q)
        self.assertIsNotNone(cache.get(cache_key))
        self.assertEqual(len(stream), 39)
        for s in stream:
            self.assertIn('programming', s.text)

    @feed_response('instagram', modifier=_tamper_date)
    def test_feed_unexpected_date_format(self, feed):
        stream = self.stream.get_items(config=self.feedconfig)
        self.assertIsNone(stream[0].posted)

    @feed_response('instagram', modifier=_remove_items)
    def test_feed_unexpected_response(self, feed):
        with self.assertRaises(FeedError):
            self.stream.get_items(config=self.feedconfig)
