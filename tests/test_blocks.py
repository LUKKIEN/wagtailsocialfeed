"""
test_blocks
----------------------------------

Tests for `wagtailsocialfeed.blocks`.
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
        self.assertIn("Please try out 1.6 on your staging sites ahead of the",
                      html)
        self.assertIn("Congratulations to Wagtail users @britishswimming!",
                      html)
        self.assertIn("When are *you* going to write a blog post for us?",
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
