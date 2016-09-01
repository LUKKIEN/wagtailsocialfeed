from __future__ import unicode_literals

from django.conf.urls import include, url
from django.core.urlresolvers import reverse
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.wagtailadmin.menu import Menu, MenuItem, SubmenuMenuItem
from wagtail.wagtailcore import hooks

from . import urls
from .models import SocialFeedConfiguration
from django.db.models.signals import post_save


class SocialFeedConfigurationAdmin(ModelAdmin):
    model = SocialFeedConfiguration
    menu_label = 'Social feeds'  # TODO ditch this to use verbose_name_plural from model # NOQA
    menu_icon = 'icon icon-fa-rss'
    menu_order = 400
    add_to_settings_menu = True
    list_display = ('source', 'username')
    list_filter = ('source', )


class SocialFeedModerateMenu(Menu):
    config_menu_items = {
        # Contains all submenu items mapped to the id's of the
        # `SocialFeedConfiguration` they link to
    }

    def __init__(self):
        # Iterate over existing configurations that are moderated
        config_qs = SocialFeedConfiguration.objects.filter(moderated=True)
        for config in config_qs:
            self.config_menu_items[config.id] = \
                self._create_moderate_menu_item(config)

        self._registered_menu_items = list(self.config_menu_items.values())
        self.construct_hook_name = None

        post_save.connect(self._update_menu, sender=SocialFeedConfiguration)

    def _update_menu(self, instance, **kwargs):
        """
        Call whenever a `SocialFeedCongiration` gets changed.

        When it is not moderated anymore, but exists in our menu, it should be
        removed.
        When it is moderated but does not exist yet, we should create a
        new menu item.
        """
        has_menu_item = instance.id in self.config_menu_items.keys()

        if not instance.moderated and has_menu_item:
            menu_item = self.config_menu_items.pop(instance.id)
            index = self._registered_menu_items.index(menu_item)
            del self._registered_menu_items[index]
        elif instance.moderated and not has_menu_item:
            menu_item = self._create_moderate_menu_item(instance)
            self.config_menu_items[instance.id] = menu_item
            self._registered_menu_items.append(menu_item)

    def _create_moderate_menu_item(self, config):
        """Create a submenu item for the moderate admin page."""
        url = reverse('wagtailsocialfeed:moderate', kwargs={'pk': config.pk})
        return MenuItem(six.text_type(config), url,
                        classnames='icon icon-folder-inverse')


modeladmin_register(SocialFeedConfigurationAdmin)


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^socialfeed/', include(urls, app_name='wagtailsocialfeed',
            namespace='wagtailsocialfeed')),
    ]


@hooks.register('register_admin_menu_item')
def register_socialfeed_menu():
    # Create the main socialfeed menu item
    socialfeed_menu = SocialFeedModerateMenu()
    return SubmenuMenuItem(
        _('Social feed'), socialfeed_menu, classnames='icon icon-fa-rss',
        order=800)
