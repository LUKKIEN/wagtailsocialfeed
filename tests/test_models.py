"""
test_models
----------------------------------

Tests for `wagtailsocialfeed.models`.
"""
from __future__ import unicode_literals

from django.test import RequestFactory, TestCase
from django.utils import six

from wagtailsocialfeed.utils.feed.factory import FeedFactory

from . import feed_response
from .factories import SocialFeedConfigurationFactory, SocialFeedPageFactory


class SocialFeedConfigurationTest(TestCase):
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


class ModeratedItemTest(TestCase):
    @feed_response('twitter')
    def setUp(self, tweets):
        self.feedconfig = SocialFeedConfigurationFactory(
            source='twitter', username='wagtailcms')
        feed = FeedFactory.create('twitter')
        items = feed.get_items(self.feedconfig)
        self.item, created = self.feedconfig.moderated_items.get_or_create_for(items[0].serialize())

    def test_str(self):
        self.assertEqual(
            six.text_type(self.item),
            "ModeratedItem<twitter> (779235925826138112 posted 2016-09-23 08:28:16+00:00)")


class SocialFeedPageTest(TestCase):
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
        items = feed.get_items(self.feedconfig)
        for item in items[:3]:
            self.feedconfig.moderated_items.get_or_create_for(
                item.serialize())

        resp = self.page.serve(request)
        resp.render()
        self.assertIn('feed', resp.context_data)
        self.assertEqual(len(resp.context_data['feed']), 3)
