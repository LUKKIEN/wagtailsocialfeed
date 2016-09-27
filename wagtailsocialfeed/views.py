from __future__ import unicode_literals

from django.http import JsonResponse
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from django.views.generic.detail import DetailView

from wagtail.wagtailadmin.forms import SearchForm

from .models import ModeratedItem, SocialFeedConfiguration
from .utils.feed.factory import FeedFactory


class ModerateView(DetailView):
    """
    ModerateView.

    Collect the latest feeds and find out which ones are already
    moderated/allowed in the feed (already have an `ModeratedItem`
    associated with them
    """

    template_name = 'wagtailsocialfeed/admin/moderate.html'
    queryset = SocialFeedConfiguration.objects.filter(moderated=True)

    def page_title(self):
        return _('Moderating {}').format(self.object)

    def get_search_form(self):
        if 'q' in self.request.GET:
            return SearchForm(self.request.GET, placeholder=_("Search posts"))
        return SearchForm(placeholder=_("Search posts"))

    def get_context_data(self, **kwargs):
        context = super(ModerateView, self).get_context_data(**kwargs)
        feed = FeedFactory.create(self.object.source)

        form = self.get_search_form()
        query_string = None
        use_cache = True

        if form.is_valid():
            use_cache = False
            query_string = form.cleaned_data['q']

        items = feed.get_items(config=self.object, query_string=query_string,
                               use_cache=use_cache)

        if self.object.moderated:
            allowed_ids = self.object.moderated_items.values_list(
                'external_id', flat=True)
            for item in items:
                # Flag to see if this item is already allowed in
                # the feed or not
                item.allowed = item.id in allowed_ids

        context['feed'] = items
        context['search_form'] = form

        return context

error_messages = {
    'no_original':
        _('The original social feed post was not found in the POST data'),
    'not_found': _('The moderated item with the given id could not be found')
}


class ModerateAllowView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(ModerateAllowView, self).dispatch(*args, **kwargs)

    def post(self, request, pk, post_id):
        config = SocialFeedConfiguration.objects.get(pk=pk)

        if 'original' not in request.POST:
            err = {'message': six.text_type(error_messages['no_original'])}
            return JsonResponse(err, status=400)

        original = request.POST['original']
        item, created = config.moderated_items.get_or_create_for(original)

        return JsonResponse({
            'message': 'The post is now allowed on the feed',
            'post_id': post_id,
            'allowed': True
        })


class ModerateRemoveView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(ModerateRemoveView, self).dispatch(*args, **kwargs)

    def post(self, request, pk, post_id):
        config = SocialFeedConfiguration.objects.get(pk=pk)

        try:
            item = config.moderated_items.get(external_id=post_id)
        except ModeratedItem.DoesNotExist:
            err = {'message': six.text_type(error_messages['not_found'])}
            return JsonResponse(err, status=404)

        item.delete()

        return JsonResponse({
            'message': 'The post is removed from the feed',
            'post_id': post_id,
            'allowed': False
        })
