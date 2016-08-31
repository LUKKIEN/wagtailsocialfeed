from __future__ import unicode_literals

from django.conf.urls import include, url
from django.core.urlresolvers import reverse
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from wagtail.contrib.modeladmin.menus import SubMenu
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.wagtailadmin.menu import MenuItem, SubmenuMenuItem
from wagtail.wagtailcore import hooks

from . import urls
from .models import SocialFeedConfiguration


class SocialFeedConfigurationAdmin(ModelAdmin):
    model = SocialFeedConfiguration
    menu_label = 'Social feeds'  # TODO ditch this to use verbose_name_plural from model # NOQA
    menu_icon = 'icon icon-fa-rss'
    menu_order = 400
    add_to_settings_menu = True
    list_display = ('source', 'username')
    list_filter = ('source', )

modeladmin_register(SocialFeedConfigurationAdmin)


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^socialfeed/', include(urls, app_name='wagtailsocialfeed',
            namespace='wagtailsocialfeed')),
    ]


@hooks.register('register_admin_menu_item')
def register_socialfeed_menu():
    config_menu_items = []
    config_qs = SocialFeedConfiguration.objects.filter(moderated=True)
    for config in config_qs:
        url = reverse('wagtailsocialfeed:moderate', kwargs={'pk': config.pk})
        config_menu_items.append(
            MenuItem(six.text_type(config), url,
                     classnames='icon icon-folder-inverse')
        )

    socialfeed_menu = SubMenu(config_menu_items)
    return SubmenuMenuItem(
        _('Social feed'), socialfeed_menu, classnames='icon icon-fa-rss',
        order=800)
