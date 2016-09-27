from __future__ import unicode_literals

from django import forms

from wagtail.wagtailcore import blocks

from .models import SocialFeedConfiguration
from .utils import get_feed_items


class FeedChooserBlock(blocks.ChooserBlock):
    target_model = SocialFeedConfiguration
    widget = forms.Select

    def value_for_form(self, value):
        if value:
            return value.pk
        return None

    def to_python(self, value):
        return self.target_model.objects.get(pk=value)


class SocialFeedBlock(blocks.StructBlock):
    feedconfig = FeedChooserBlock()
    limit = blocks.IntegerBlock(required=False, min_value=0)

    class Meta:
        icon = 'icon icon-fa-rss'
        template = 'wagtailsocialfeed/social_feed_block.html'

    def get_context(self, value):
        context = super(SocialFeedBlock, self).get_context(value)

        feedconfig = value['feedconfig']
        context['feed'] = get_feed_items(feedconfig, limit=value['limit'])

        return context
