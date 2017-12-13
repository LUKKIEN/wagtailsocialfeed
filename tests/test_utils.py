from django.test import TestCase

from wagtailsocialfeed.models import SocialFeedConfiguration
from wagtailsocialfeed.utils import get_feed_items, get_feed_items_mix
from wagtailsocialfeed.utils.feed.factory import FeedFactory

from . import feed_response
from .factories import SocialFeedConfigurationFactory


class UtilTest(TestCase):
    """Test util methods."""
    def setUp(self):
        self.feedconfig = SocialFeedConfigurationFactory.create(
            source='twitter',
            username='someuser')

    @feed_response('twitter')
    def test_get_feed_items(self, tweets):
        items = get_feed_items(self.feedconfig)
        self.assertEquals(len(items), len(tweets))

    @feed_response(['twitter', 'instagram'])
    def test_get_feed_items_mix(self, tweets, instagram_posts):
        items = get_feed_items_mix(SocialFeedConfiguration.objects.all())
        # There is only a twitter configuration, so should just return the twitter items
        self.assertEquals(len(items), len(tweets))

        SocialFeedConfigurationFactory.create(
            source='instagram',
            username='someuser')
        items = get_feed_items_mix(SocialFeedConfiguration.objects.all())
        self.assertEquals(len(items), len(tweets) + len(instagram_posts))

        # Check if the date order is correct
        last_date = None
        for item in items:
            if last_date:
                self.assertLessEqual(item.posted, last_date)
            last_date = item.posted

    @feed_response(['twitter', 'instagram'])
    def test_get_feed_items_mix_moderated(self, tweets, instagram_posts):
        """Test the feed mix with one of the sources being moderated."""
        instagramconfig = SocialFeedConfigurationFactory.create(
            source='instagram',
            username='someuser',
            moderated=True)

        items = get_feed_items_mix(SocialFeedConfiguration.objects.all())

        # None of the instagram posts are moderated, so should only
        # return the twitter posts
        self.assertEquals(len(items), len(tweets))
        instagram_feed = FeedFactory.create('instagram')
        instagram_items = instagram_feed.get_items(instagramconfig)
        for item in instagram_items[:3]:
            instagramconfig.moderated_items.get_or_create_for(
                item.serialize())

        items = get_feed_items_mix(SocialFeedConfiguration.objects.all())
        self.assertEquals(len(items), len(tweets) + 3)
        # Check if the date order is correct
        last_date = None
        for item in items:
            if last_date:
                self.assertLessEqual(item.posted, last_date)
            last_date = item.posted
        self.assertEquals(len([i for i in items if i.type == 'instagram']), 3)
