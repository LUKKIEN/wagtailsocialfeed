"""
test_models
----------------------------------

Tests for `wagtailsocialfeed.models`.
"""
from __future__ import unicode_literals

import json

from django.test import RequestFactory, TestCase
from django.utils import six

from wagtailsocialfeed.utils.feed.factory import FeedFactory

from . import date_handler, feed_response
from .factories import SocialFeedConfigurationFactory, SocialFeedPageFactory


class TestSocialFeedConfiguration(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        twitter_config = SocialFeedConfigurationFactory.create(
            source='twitter', username='johndoe')
        instagram_config = SocialFeedConfigurationFactory.create(
            source='instagram', username='johndoe')

        self.assertEqual(six.text_type(twitter_config),
                         'twitter (@johndoe)')
        self.assertEqual(six.text_type(instagram_config),
                         'instagram (johndoe)')


class TestSocialFeedPage(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.feedconfig = SocialFeedConfigurationFactory(
            source='twitter', username='wagtailcms')
        self.page = SocialFeedPageFactory.create(feedconfig=self.feedconfig)

    @feed_response('twitter')
    def test_serve(self, tweets):
        request = self.factory.get('/pages/feed/')
        resp = self.page.serve(request)
        resp.render()

        self.assertIn('feed', resp.context_data)
        self.assertEqual(len(resp.context_data['feed']), 17)

    @feed_response('twitter')
    def test_serve_moderated(self, tweets):
        self.feedconfig.moderated = True
        self.feedconfig.save()

        request = self.factory.get('/pages/feed/')
        resp = self.page.serve(request)
        resp.render()
        self.assertIn('feed', resp.context_data)
        self.assertEqual(len(resp.context_data['feed']), 0)

        # Now moderate some items
        feed = FeedFactory.create('twitter')
        stream = feed.get_feed(self.feedconfig)
        for item in stream[:3]:
            self.feedconfig.moderated_items.get_or_create_for(
                json.dumps(item, default=date_handler))

        resp = self.page.serve(request)
        resp.render()
        self.assertIn('feed', resp.context_data)
        self.assertEqual(len(resp.context_data['feed']), 3)
