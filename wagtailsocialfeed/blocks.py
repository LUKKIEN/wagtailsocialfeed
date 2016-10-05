from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailcore import blocks

from .models import SocialFeedConfiguration
from .utils import get_feed_items, get_feed_items_mix


class FeedChooserBlock(blocks.ChooserBlock):
    target_model = SocialFeedConfiguration
    widget = forms.Select

    def value_for_form(self, value):
        if value:
            if isinstance(value, int):
                return value
            return value.pk
        return None

    def value_from_form(self, value):
        if value is None or isinstance(value, self.target_model):
            return value
        try:
            value = int(value)
        except ValueError:
            return None

        try:
            return self.target_model.objects.get(pk=value)
        except self.target_model.DoesNotExist:
            return None

    def to_python(self, value):
        if value:
            return self.target_model.objects.get(pk=value)
        return None


class SocialFeedBlock(blocks.StructBlock):
    feedconfig = FeedChooserBlock(
        required=False,
        help_text=_("Select a feed configuration to show. Leave blank to show a mix of all the feeds"))
    limit = blocks.IntegerBlock(required=False, min_value=0)

    class Meta:
        icon = 'icon icon-fa-rss'
        template = 'wagtailsocialfeed/social_feed_block.html'

    def get_context(self, value):
        context = super(SocialFeedBlock, self).get_context(value)

        feedconfig = value['feedconfig']
        feed = None
        if feedconfig:
            feed = get_feed_items(feedconfig, limit=value['limit'])
        else:
            feed = get_feed_items_mix(SocialFeedConfiguration.objects.all(),
                                      limit=value['limit'])

        context['feed'] = feed

        return context
