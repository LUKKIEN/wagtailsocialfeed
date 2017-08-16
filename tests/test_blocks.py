"""
test_blocks
----------------------------------

Tests for `wagtailsocialfeed.blocks`.

In Wagtail 1.8 Function accepting only one parameter and that's why its raising TypeError
In Combination of Django 1.11 and Wagtail 1.9, `ImportError` Exception is occurring in wagtailimage.

from django.forms.widgets import flatatt
ImportError: cannot import name flatatt

because it's moved to utils

"""

from __future__ import unicode_literals

from django.test import RequestFactory, TestCase

from bs4 import BeautifulSoup
from wagtailsocialfeed.blocks import SocialFeedBlock

from . import feed_response
from .factories import SocialFeedConfigurationFactory, SocialFeedPageFactory


class TestSocialFeedBlock(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.feedconfig = SocialFeedConfigurationFactory(
            source='twitter', username='wagtailcms')
        self.page = SocialFeedPageFactory.create(feedconfig=self.feedconfig)

    @feed_response('twitter')
    def test_render(self, tweets):
        block = SocialFeedBlock()
        value = {
            'feedconfig': self.feedconfig,
            'limit': 3
        }
        context = block.get_context(value)
        html = block.render(value)

        self.assertEqual(len(context['feed']), 3)
        self.assertIn("snipcart our pleasure! also posted to",
                      html)
        self.assertIn("&quot;It&#39;s elegant, flexible, and, IMHO, kicks ass&quot;",
                      html)
        self.assertIn("@snipcart your new Wagtail + Snipcart tutorial is awesssssome",
                      html)

    def test_to_python(self):
        block = SocialFeedBlock()
        value = {
            'feedconfig': self.feedconfig.pk,
            'limit': 3
        }
        result = block.to_python(value)
        self.assertEqual(result['feedconfig'], self.feedconfig)
        self.assertEqual(result['limit'], 3)

    def test_render_form(self):
        block = SocialFeedBlock()
        value = {
            'feedconfig': self.feedconfig,
            'limit': 3
        }
        html = block.render_form(value, prefix='test')
        soup = BeautifulSoup(html, 'html.parser')

        self.assertEqual(
            soup.find(id='test-feedconfig').find_all('option')[1].text,
            'twitter (@wagtailcms)')

    @feed_response('twitter')
    def test_get_context_with_parent_context(self, tweets):
        block = SocialFeedBlock()

        value = {
            'feedconfig': self.feedconfig,
            'limit': 3
        }
        parent_context = {'has_parent': 'parent context'}

        try:
            context = block.get_context(value, parent_context)
            self.assertEqual(context['has_parent'], parent_context['has_parent'])
            # In Wagtail 1.8 Function accepting only one parameter and that's why its raising TypeError
        except TypeError:
            self.skipTest(TestSocialFeedBlock)

    @feed_response('twitter')
    def test_get_context_without_parent_context(self, tweets):
        block = SocialFeedBlock()

        value = {
            'feedconfig': self.feedconfig,
            'limit': 3
        }

        context = block.get_context(value)
        self.assertEqual(context['value'], value)
