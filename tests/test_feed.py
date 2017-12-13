import datetime
import json
import re

import responses
from dateutil.tz import tzutc
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from wagtailsocialfeed.utils.feed import AbstractFeed, FeedError, FeedItem
from wagtailsocialfeed.utils.feed.facebook import (FacebookFeed,
                                                   FacebookFeedItem)
from wagtailsocialfeed.utils.feed.factory import FeedFactory
from wagtailsocialfeed.utils.feed.instagram import (InstagramFeed,
                                                    InstagramFeedItem)
from wagtailsocialfeed.utils.feed.twitter import TwitterFeed, TwitterFeedItem

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
        self.assertIsInstance(FeedFactory.create('facebook'), FacebookFeed)
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
        self.assertEqual(stream[-1].image_dict['small']['width'], 680)
        self.assertEqual(stream[-1].image_dict['small']['height'], 546)

        self.assertEqual(stream[-1].image_dict['thumb']['url'],
                         base_url + ":thumb")
        self.assertEqual(stream[-1].image_dict['thumb']['width'], 150)
        self.assertEqual(stream[-1].image_dict['thumb']['height'], 150)

        self.assertEqual(stream[-1].image_dict['medium']['url'],
                         base_url + ":medium")
        self.assertEqual(stream[-1].image_dict['medium']['width'], 1200)
        self.assertEqual(stream[-1].image_dict['medium']['height'], 963)

        self.assertEqual(stream[-1].image_dict['large']['url'],
                         base_url + ":large")
        self.assertEqual(stream[-1].image_dict['large']['width'], 2048)
        self.assertEqual(stream[-1].image_dict['large']['height'], 1643)

        #The following data is not explicitly stored, but should still be accessible
        self.assertEqual(stream[0].in_reply_to_user_id, 1252591452)

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

        # Ensure we set the SEARCH_MAX_HISTORY big enough for both twitter
        # pages to be included
        now = datetime.datetime.now(tzutc())
        last_post_date = TwitterFeedItem.get_post_date(page2[-1])
        delta = (now - last_post_date) + datetime.timedelta(seconds=10)
        with override_settings(WAGTAIL_SOCIALFEED_SEARCH_MAX_HISTORY=delta):
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
    resp['user']['media']['nodes'][0]['date'] = "not_a_timestamp"
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
        self.assertEqual(len(stream), 12)
        for item in stream:
            assert isinstance(item, FeedItem)
        self.assertEqual(
            stream[0].posted,
            datetime.datetime(2017, 11, 15, 21, 55, 44, tzinfo=timezone.utc))
        self.assertEqual(stream[0].image_dict['small']['src'],
                         "https://scontent-amt2-1.cdninstagram.com/t51.2885-15/s320x320/e35/c86.0.908.908/23507082_173663316554801_3781761610851287040_n.jpg" # NOQA
                         )
        self.assertEqual(stream[0].image_dict['thumb']['src'],
                         "https://scontent-amt2-1.cdninstagram.com/t51.2885-15/s240x240/e35/c86.0.908.908/23507082_173663316554801_3781761610851287040_n.jpg" # NOQA
                         )
        self.assertEqual(stream[0].image_dict['medium']['src'],
                         "https://scontent-amt2-1.cdninstagram.com/t51.2885-15/s480x480/e35/c86.0.908.908/23507082_173663316554801_3781761610851287040_n.jpg" # NOQA
                         )

        # The following data is not explicitly stored, but should still be accessible
        self.assertEqual(stream[0].code, "Bbh7J7JlCRn")

    @feed_response('instagram', modifier=_tamper_date)
    def test_feed_unexpected_date_format(self, feed):
        stream = self.stream.get_items(config=self.feedconfig)
        self.assertIsNone(stream[0].posted)

    @feed_response('instagram', modifier=_remove_items)
    def test_feed_unexpected_response(self, feed):
        with self.assertRaises(FeedError):
            self.stream.get_items(config=self.feedconfig)


class FacebookFeedTest(TestCase):
    def setUp(self):
        cache.clear()
        self.feedconfig = SocialFeedConfigurationFactory.create(
            source='facebook')
        self.stream = FeedFactory.create('facebook')
        self.cache_key = 'socialfeed:{}:data:{}'.format('FacebookFeed', self.feedconfig.id)

    @feed_response('facebook')
    def test_feed(self, feed):
        self.assertIsNone(cache.get(self.cache_key))

        stream = self.stream.get_items(config=self.feedconfig)

        self.assertIsNotNone(cache.get(self.cache_key))
        self.assertEqual(len(stream), 25)

        for item in stream:
            self.assertIsInstance(item, FeedItem)
        self.assertEqual(
            stream[0].posted,
            datetime.datetime(2016, 10, 4, 14, 48, 9, tzinfo=timezone.utc))

        self.assertEqual(stream[0].image_dict['thumb']['url'],
                         "https://scontent.xx.fbcdn.net/v/t1.0-0/s130x130/14606290_1103282596374848_3084561525150401400_n.jpg?oh=4a993e12211341d2304724a5822b1fbf&oe=58628491" # NOQA
                         )

        # The following data is not explicitly stored, but should still be accessible
        self.assertEqual(stream[0].icon, "https://www.facebook.com/images/icons/photo.gif")

    @responses.activate
    @override_settings(WAGTAIL_SOCIALFEED_SEARCH_MAX_HISTORY=datetime.timedelta(weeks=500))
    def test_search(self):
        with open('tests/fixtures/facebook.json', 'r') as feed_file:
            page1 = json.loads("".join(feed_file.readlines()))
        with open('tests/fixtures/facebook.2.json', 'r') as feed_file:
            page2 = json.loads("".join(feed_file.readlines()))

        responses.add(
            responses.GET,
            re.compile('(?!.*paging_token)https?://graph.facebook.com.*'),
            json=page1, status=200)

        responses.add(
            responses.GET,
            re.compile('(?=.*paging_token)https?://graph.facebook.com.*'),
            json=page2, status=200)

        q = "tutorials"
        cache_key = "{}:q-{}".format(self.cache_key, q)

        self.assertIsNone(cache.get(cache_key))
        # Ensure we set the SEARCH_MAX_HISTORY big enough for both facebook
        # pages to be included
        now = datetime.datetime.now(tzutc())
        last_post_date = FacebookFeedItem.get_post_date(page2['data'][-1])
        delta = (now - last_post_date) + datetime.timedelta(seconds=10)
        with override_settings(WAGTAIL_SOCIALFEED_SEARCH_MAX_HISTORY=delta):
            stream = self.stream.get_items(config=self.feedconfig,
                                           query_string=q)

        self.assertIsNotNone(cache.get(cache_key))
        self.assertEqual(len(stream), 2)
        for s in stream:
            self.assertIn('tutorials', s.text)
