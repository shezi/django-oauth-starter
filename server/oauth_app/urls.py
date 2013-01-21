from django.conf.urls import patterns, include, url
from oauth_app import views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^oauth/request_token/$', views.request_token, name='oauth-request-token'),
    url(r'^oauth/request_token/(?P<token_key>[0-9a-f]+)/status/$', views.request_token_status, name='oauth-request-token-status'),
    url(r'^oauth/access_token/$', views.access_token, name='oauth-access-token'),

    # the following two are test resources. You can expose them for testing clients, if you want.
    url(r'^oauth/access_test_resource/$', views.access_test_resource, name='oauth-test-resource'),
    url(r'^oauth/access_test_resource_bare/$', views.access_test_resource_bare, name='oauth-test-resource'),

)

# disable these and put them in your own app
# and don't forget to implement the views: the authorization/deauthorization views here are only suggestions
urlpatterns += patterns('',

    url(r'^oauth/authorize/$', views.authorize, name='oauth-authorize-request'),
    url(r'^oauth/clients/$', views.clients, name='oauth-client-list'),
    url(r'^oauth/deauthorize/(?P<token_key>[0-9a-f]+)/$', views.deauthorize, name='oauth-deauthorize-access'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'oauth/login.html', }, name='login'),

)
