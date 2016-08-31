from __future__ import absolute_import, unicode_literals
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^moderate/(?P<pk>\d+)/$',
        views.ModerateView.as_view(),
        name='moderate'),
    url(r'^moderate/(?P<pk>\d+)/(?P<post_id>.+)/allow/$',
        views.ModerateAllowView.as_view(),
        name='allow'),
    url(r'^moderate/(?P<pk>\d+)/(?P<post_id>.+)/remove/$',
        views.ModerateRemoveView.as_view(),
        name='remove'),
]
