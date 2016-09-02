from __future__ import unicode_literals

import json

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.encoding import force_text

from bs4 import BeautifulSoup
from wagtailsocialfeed.models import ModeratedItem
from wagtailsocialfeed.utils.feed.factory import FeedFactory

from . import date_handler, feed_response
from .factories import SocialFeedConfigurationFactory


class ModerateTestMixin(object):
    def setUp(self):
        self.feedconfig = SocialFeedConfigurationFactory.create(
            source='twitter',
            username='wagtailcms',
            moderated=True)

        self.user = get_user_model().objects.create_user(
            'john', 'john@doe.com', 'test')
        self.admin = get_user_model().objects.create_superuser(
            'admin', 'admin@doe.com', 'test')


class ModerateViewTest(ModerateTestMixin, TestCase):
    def setUp(self):
        super(ModerateViewTest, self).setUp()
        self.url = reverse('wagtailsocialfeed:moderate',
                           kwargs={'pk': self.feedconfig.id})

    def test_permissions(self):
        resp = self.client.get(self.url)
        self.assertRedirects(resp, '/cms/login/?next={}'.format(self.url))

        self.client.login(username='john', password='test')
        resp = self.client.get(self.url)
        self.assertRedirects(resp, '/cms/login/?next={}'.format(self.url))

    def test_404(self):
        self.feedconfig.moderated = False
        self.feedconfig.save()
        self.client.login(username='admin', password='test')

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 404)

    @feed_response('twitter')
    def test_view(self, tweets):
        self.client.login(username='admin', password='test')

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(resp.content, 'html.parser')

        # The original post should be included to be used for
        # moderated allow/remove
        rows = soup.tbody.find_all('tr')

        # Substract the columns from the first row/tweet
        columns = rows[0].find_all('td')
        post_id = tweets[0]['id']
        self.assertEqual(columns[0].input['id'],
                         'post_original_{}'.format(post_id))

        url_allow = reverse('wagtailsocialfeed:allow',
                            kwargs={'pk': self.feedconfig.id,
                                    'post_id': post_id})
        url_remove = reverse('wagtailsocialfeed:remove',
                             kwargs={'pk': self.feedconfig.id,
                                     'post_id': post_id})

        allow_a_element = columns[0].find(attrs={'class': 'action-allow'})
        remove_a_element = columns[0].find(attrs={'class': 'action-remove'})
        self.assertEqual(allow_a_element['href'], url_allow)
        self.assertEqual(remove_a_element['href'], url_remove)

    # @feed_response('twitter')
    # def test_post_allow(self, tweets):
    #     self.client.login(username='admin', password='test')
    #     resp = self.client.get(self.url)
    #     soup = BeautifulSoup(resp.content, 'html.parser')
    #     rows = soup.tbody.find_all('tr')
    #     columns = rows[0].find_all('td')
    #     post_id = tweets[0]['id']

    #     url_allow = reverse('wagtailsocialfeed:allow',
    #                         kwargs={'pk': self.feedconfig.id,
    #                                 'post_id': post_id})
    #     print columns[0].input['value']


class ModerateAllowViewTest(ModerateTestMixin, TestCase):
    @feed_response('twitter')
    def setUp(self, tweets):
        super(ModerateAllowViewTest, self).setUp()
        self.feed = FeedFactory.create('twitter')
        self.items = self.feed.get_items(self.feedconfig)
        self.post = self.items[0]
        self.url = reverse('wagtailsocialfeed:allow',
                           kwargs={'pk': self.feedconfig.id,
                                   'post_id': self.post['id']})

    def test_post_permissions(self):
        resp = self.client.post(self.url)
        self.assertRedirects(resp, '/cms/login/?next={}'.format(self.url))

        self.client.login(username='john', password='test')
        resp = self.client.post(self.url)
        self.assertRedirects(resp, '/cms/login/?next={}'.format(self.url))

    def test_http_methods(self):
        self.client.login(username='admin', password='test')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)

    def test_post(self):
        self.client.login(username='admin', password='test')

        # Sanity check
        self.assertEqual(ModeratedItem.objects.count(), 0)

        # Test with missing data
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 400)
        json_resp = json.loads(force_text(resp.content))
        self.assertEqual(
            json_resp['message'],
            'The original social feed post was not found in the POST data')

        # Now for the correct way
        data = {
            'original': json.dumps(self.post, default=date_handler)
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ModeratedItem.objects.count(), 1)

        # Idempotent?
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ModeratedItem.objects.count(), 1)


class ModerateRemoveViewTest(ModerateTestMixin, TestCase):
    @feed_response('twitter')
    def setUp(self, tweets):
        super(ModerateRemoveViewTest, self).setUp()
        self.feed = FeedFactory.create('twitter')
        self.items = self.feed.get_items(self.feedconfig)
        self.post = self.items[0]
        self.post_serialized = json.dumps(self.post, default=date_handler)
        self.feedconfig.moderated_items.get_or_create_for(self.post_serialized)
        self.url = reverse('wagtailsocialfeed:remove',
                           kwargs={'pk': self.feedconfig.id,
                                   'post_id': self.post['id']})

    def test_post_permissions(self):
        resp = self.client.post(self.url)
        self.assertRedirects(resp, '/cms/login/?next={}'.format(self.url))

        self.client.login(username='john', password='test')
        resp = self.client.post(self.url)
        self.assertRedirects(resp, '/cms/login/?next={}'.format(self.url))

    def test_http_methods(self):
        self.client.login(username='admin', password='test')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)

    def test_post(self):
        self.client.login(username='admin', password='test')

        # Sanity check
        self.assertEqual(ModeratedItem.objects.count(), 1)

        # Test with missing data
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ModeratedItem.objects.count(), 0)

        # Should not be found
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 404)
