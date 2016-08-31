from __future__ import unicode_literals

import factory

from wagtailsocialfeed.models import SocialFeedConfiguration, SocialFeedPage


class SocialFeedConfigurationFactory(factory.DjangoModelFactory):
    username = factory.Faker('user_name')

    class Meta:
        model = SocialFeedConfiguration


class SocialFeedPageFactory(factory.DjangoModelFactory):
    title = factory.Faker('word')
    path = '0000'
    depth = 0

    feedconfig = factory.SubFactory(SocialFeedConfigurationFactory)

    class Meta:
        model = SocialFeedPage
