"""Authentication functions for our own authentication schemes"""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

import rest_framework.authentication

from oauth_app import oauth, oauth_datastore



class OAuth10aAuthentication(rest_framework.authentication.BaseAuthentication):
    """Verify against our OAuth implementation."""

    # configuration
    oauth_server = oauth.OAuthServer(oauth_datastore.DjangoOAuthDataStore())
    oauth_server.add_signature_method(oauth.OAuthSignatureMethod_PLAINTEXT())
    oauth_server.add_signature_method(oauth.OAuthSignatureMethod_HMAC_SHA1())
    
    
    def get_oauth_request(self, request):
        """Read the data from the request and transform it into an OAuth authentication request if possible."""
    
        getdata = {}
        for k in request.REQUEST.keys():
            getdata[k] = request.REQUEST.get(k)
        oauth_request = oauth.OAuthRequest.from_request(request.method, request.build_absolute_uri(request.path), headers=request.META, query_data=getdata)
    
        return oauth_request
    
    
    def authenticate(self, request):
        oauth_request = oauth.OAuthRequest.from_request(request)
        try:
            # verify the request has been oauth authorized
            consumer, token, params = self.oauth_server.verify_request(oauth_request)

            # no error here means we can go on: the user for our token is the user we want!
            return token.user, token

        except oauth.OAuthError, err:
            print err
            return None
        