from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailcore.models import Page

from .utils.feed.factory import FeedItemFactory
from .utils import get_feed_items
from .managers import ModeratedItemManager


@python_2_unicode_compatible
class SocialFeedConfiguration(models.Model):
    FEED_CHOICES = (
        ('twitter', _('Twitter')),
        ('instagram', _('Instagram')),
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

    def get_content(self):
        if not hasattr(self, '_feeditem'):
            item_cls = FeedItemFactory.get_class(self.config.source)
            self._feeditem = item_cls.from_moderated(self)
        return self._feeditem


class SocialFeedPage(Page):
    feedconfig = models.ForeignKey(SocialFeedConfiguration,
                                   blank=False,
                                   null=False,
                                   on_delete=models.PROTECT)

    content_panels = Page.content_panels + [
        FieldPanel('feedconfig'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(SocialFeedPage,
                        self).get_context(request, *args, **kwargs)
        context['feed'] = get_feed_items(self.feedconfig)
        return context
