import datetime

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.utils import timezone

from wagtailsocialfeed.utils.feed import AbstractFeed, FeedError
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

    def test_fetch_online(self):
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
            self.assertIn('date', item)
            self.assertIn('id', item)
            self.assertIn('text', item)
            self.assertIn('image', item)
        self.assertEqual(
            stream[0]['date'],
            datetime.datetime(2016, 8, 9, 13, 16, 33, tzinfo=timezone.utc))
        self.assertIsNone(stream[0]['image'])

        self.assertIsNotNone(stream[-2]['image'])
        base_url = 'https://pbs.twimg.com/media/CnpYVx0UkAEdCpU.jpg'

        self.assertEqual(stream[-2]['image']['small']['url'],
                         base_url + ":small")
        self.assertEqual(stream[-2]['image']['thumb']['url'],
                         base_url + ":thumb")
        self.assertEqual(stream[-2]['image']['medium']['url'],
                         base_url + ":medium")
        self.assertEqual(stream[-2]['image']['large']['url'],
                         base_url + ":large")

    @override_settings(WAGTAIL_SOCIALFEED_CONFIG={})
    def test_configuration(self):
        with self.assertRaises(ImproperlyConfigured):
            FeedFactory.create('twitter')


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
            self.assertIn('date', item)
            self.assertIn('id', item)
            self.assertIn('text', item)
            self.assertIn('image', item)
        self.assertEqual(
            stream[0]['date'],
            datetime.datetime(2016, 8, 17, 4, 31, 47, tzinfo=timezone.utc))

        self.assertEqual(stream[0]['image']['small']['url'],
                         "https://scontent-frt3-1.cdninstagram.com/t51.2885-15/s320x320/e35/14026774_1163660323707262_1160471917_n.jpg?ig_cache_key=MTMxODUzMDUxMDQyNzYzNjA2Mg%3D%3D.2.l" # NOQA
                         )
        self.assertEqual(stream[0]['image']['thumb']['url'],
                         "https://scontent-frt3-1.cdninstagram.com/t51.2885-15/s150x150/e35/c136.0.448.448/14032893_1190601567673451_1118658827_n.jpg?ig_cache_key=MTMxODUzMDUxMDQyNzYzNjA2Mg%3D%3D.2.c" # NOQA
                         )
        self.assertEqual(stream[0]['image']['medium']['url'],
                         "https://scontent-frt3-1.cdninstagram.com/t51.2885-15/s640x640/sh0.08/e35/14026774_1163660323707262_1160471917_n.jpg?ig_cache_key=MTMxODUzMDUxMDQyNzYzNjA2Mg%3D%3D.2.l" # NOQA
                         )

    @feed_response('instagram', modifier=_tamper_date)
    def test_feed_unexpected_date_format(self, feed):
        stream = self.stream.get_items(config=self.feedconfig)
        self.assertIsNone(stream[0]['date'])

    @feed_response('instagram', modifier=_remove_items)
    def test_feed_unexpected_response(self, feed):
        with self.assertRaises(FeedError):
            self.stream.get_items(config=self.feedconfig)
