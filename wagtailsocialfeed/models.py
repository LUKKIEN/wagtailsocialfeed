from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.functional import cached_property
from django.utils.six import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailcore.models import Page

from .managers import ModeratedItemManager
from .utils import get_feed_items, get_feed_items_mix
from .utils.feed.factory import FeedItemFactory


@python_2_unicode_compatible
class SocialFeedConfiguration(models.Model):
    FEED_CHOICES = (
        ('twitter', _('Twitter')),
        ('instagram', _('Instagram')),
        ('facebook', _('Facebook'))
    )

    source = models.CharField(_('Feed source'),
                              max_length=100,
                              choices=FEED_CHOICES,
                              blank=False)
    username = models.CharField(_('User to track'),
                                max_length=255,
                                blank=False)
    moderated = models.BooleanField(default=False)

    def __str__(self):
        name = self.username
        if self.source == 'twitter':
            name = "@{}".format(self.username)
        return "{} ({})".format(self.source, name)


@python_2_unicode_compatible
class ModeratedItem(models.Model):
    config = models.ForeignKey(SocialFeedConfiguration,
                               related_name='moderated_items',
                               on_delete=models.CASCADE)
    moderated = models.DateTimeField(auto_now_add=True)
    posted = models.DateTimeField(blank=False, null=False)

    external_id = models.CharField(max_length=255,
                                   blank=False)
    content = models.TextField(blank=False)

    objects = ModeratedItemManager()

    class Meta:
        ordering = ['-posted', ]

    def __str__(self):
        return "{}<{}> ({} posted {})".format(
            self.__class__.__name__,
            self.type,
            self.external_id,
            self.posted
        )

    def get_content(self):
        if not hasattr(self, '_feeditem'):
            item_cls = FeedItemFactory.get_class(self.config.source)
            self._feeditem = item_cls.from_moderated(self)
        return self._feeditem

    @cached_property
    def type(self):
        return self.config.source


class SocialFeedPage(Page):
    feedconfig = models.ForeignKey(SocialFeedConfiguration,
                                   blank=True,
                                   null=True,
                                   on_delete=models.PROTECT,
                                   help_text=_("Leave blank to show all the feeds."))

    content_panels = Page.content_panels + [
        FieldPanel('feedconfig'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(SocialFeedPage,
                        self).get_context(request, *args, **kwargs)
        feed = None
        if self.feedconfig:
            feed = get_feed_items(self.feedconfig)
        else:
            feed = get_feed_items_mix(SocialFeedConfiguration.objects.all())

        context['feed'] = feed
        return context
