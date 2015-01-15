import os

from tastypie.api import Api

from django.conf import settings
from django.conf.urls import include, patterns, url
from django.http import HttpResponse

from .api import (
    UserResource, TaskResource, CompletedTaskResource,
    ActivityLogResource
)
from .views import debug_login, Status, TaskFeed

api = Api(api_name='v1')
api.register(UserResource())
api.register(TaskResource())
api.register(CompletedTaskResource())
api.register(ActivityLogResource())


def fallback(request):
    # This is sort of a hack; sorry!
    index_template_path = os.path.join(
        settings.BASE_DIR,
        '../dist/index.html'
    )
    with open(index_template_path) as index:
        return HttpResponse(index.read())


urlpatterns = patterns(
    '',
    url('^api/v1/task/feed/(?P<uuid>[^/]+)/', TaskFeed(), name='feed'),
    url('^api/', include(api.urls)),
    url('^status/', Status.as_view(), name='status'),
    url('^status/', Status.as_view(), name='status'),
    url('^', fallback),
)

if settings.DEBUG:
    # Only enabled for local development as a way to
    # get around using google's authentication
    urlpatterns.insert(
        0,
        url(
            '^debug-login/?',
            debug_login,
            name='debug_login'
        ),
    )
