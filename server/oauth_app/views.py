"""
Demonstration views for OAuth handling using Django REST Framework.



The MIT License

Copyright (c) 2013 Johannes Spielmann

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from datetime import datetime, timedelta
import pytz

from django.contrib import messages
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django import forms
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView

from oauth_app import oauth, oauth_datastore



# configuration
REQUEST_TOKEN_EXPIRY = 300 # after 300 seconds, the request tokens expire, if the user didn't authorize or decline them


oauth_datastore = oauth_datastore.DjangoOAuthDataStore()
oauth_server = oauth.OAuthServer(oauth_datastore)
# remove any that you don't like, and add any that you implemented yourself
oauth_server.add_signature_method(oauth.OAuthSignatureMethod_PLAINTEXT())
oauth_server.add_signature_method(oauth.OAuthSignatureMethod_HMAC_SHA1())



class Request_Token(APIView):
    """Create an OAuth request token.
    
    You need to submit a correct OAuth request to get a key.
    """
    
    def get(self, request):
        oauth_request = oauth.OAuthRequest.from_request(request)
        if not oauth_request:
            return Response({'reason': 'could not read OAuth data'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = oauth_server.fetch_request_token(oauth_request)
            
        except oauth.OAuthError as err:
            return Response({'reason': 'could not authenticate your request, because: %s' % err.message}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(token.to_dict())
        
    def post(self, request):
        return self.get(request)
request_token = csrf_exempt(Request_Token().as_view())

class Request_Token_Status(APIView):
    """Look up the authorization status of a given oauth request token by its key.
    
    You can use this view to poll the status of your OAuth request keys. The status will start
    out as `waiting`. Three states can follow from that:
    
    * `authorized`: The user authorized the client. Proceed with the access token.
    * `declined`: The user did not authorize the client.
    * `expired`: The user took too long in deciding whether to authorize or deny. The request token expired, please start the process again.
    
    Each of these status messages is final, so you can stop polling as soon as you see one of those.
    """
    
    def get(self, request, token_key):
        token = oauth_datastore.lookup_token('request', token_key, expired_too=True)
        if not token:
            return Response({'status': 'expired'})

        if token.status != 'expired' and token.created <= datetime.utcnow().replace(tzinfo = pytz.utc) - timedelta(seconds=REQUEST_TOKEN_EXPIRY):
            token.status = 'expired'
            token.save()
            
        return Response({'status': token.status})
request_token_status = Request_Token_Status.as_view()

class Access_Token(APIView):
    """Create an OAuth access token from your request token.
    
    You need to submit a correct OAuth request token to get a key.
    """
    
    def get(self, request):
        oauth_request = oauth.OAuthRequest.from_request(request)
        if not oauth_request:
            return Response({'reason': 'could not read OAuth data'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = oauth_server.fetch_access_token(oauth_request)
            if not token:
                return Response({'reason': 'could not read OAuth data'}, status=status.HTTP_400_BAD_REQUEST)
        except oauth.OAuthError, err:
            return Response({'reason': 'could not authenticate your request, because: %s' % err.message}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(token.to_dict())
        
    def post(self, request):
        return self.get(request)
access_token = csrf_exempt(Access_Token().as_view())


class Access_Test_Resource(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        return Response({'you': 'have access', "user": request.user.username})
access_test_resource = Access_Test_Resource.as_view()    


def access_test_resource_bare(request):
    
    oauth_request = oauth.OAuthRequest.from_request(request)
    try:
        # verify the request has been oauth authorized
        consumer, token, params = oauth_server.verify_request(oauth_request)

        # no error here means we can go on: the user for our token is the user we want!
        return HttpResponse('{"you": "have access ", "user": "%s"}' % (token.user.username, ))

    except oauth.OAuthError, err:
        print err
        return None
    


@login_required
def authorize(request):

    if request.method == "POST":
        token = oauth_datastore.lookup_token('request', request.POST.get('oauth_token'))
        if token is None:
            # TODO: nice error message
            return HttpResponseForbidden()
        if token.status != 'waiting':
            # TODO: nice error message
            return HttpResponseForbidden()
        if request.POST.get('confirm', '').lower() == 'true':
            token = oauth_server.authorize_token(token, request.user)
            messages.success(request, 'Your client was authorized for access.')
            
            data = {'verifier': token.verifier, 'callback': token.consumer.callback}
            
            return render(request, 'oauth/authorize_finished.html', data)
            
        else:
            # not confirmed is the same as denied!
            token = oauth_datastore.deauthorize_request_token(token, request.user)
            messages.success(request, 'Your client was not authorized for access.')
            if token.consumer.callback == 'oob':
                return redirect('oauth-client-list')
            else:
                return redirect(token.consumer.callback)
        

    oauth_request = oauth.OAuthRequest.from_request(request)
    try:
        # get the request token
        token = oauth_server.fetch_request_token(oauth_request)
        if token.status != 'waiting':
            # TODO: nice error message (check user, too!)
            return HttpResponseForbidden()

        data = {'oauth_token': token.key,
        }

        return render(request, 'oauth/authorize.html', data)
    except oauth.OAuthError as err:
        raise err
        # CATCH THIS ERROR! and display something nice and explaining!

@login_required
def deauthorize(request, token_key):
    """Deauthorize the access token with the given access key.
    """
    data = {}
    
    token = oauth_datastore.lookup_token('access', token_key)
    
    if not token or token.user != request.user:
        # TODO: nice error message
        return HttpResponseForbidden()

    if request.method == 'POST':
        oauth_datastore.deauthorize_access_token(token)
        return redirect('oauth-client-list')

    data['key'] = token.key
    return render(request, 'oauth/deauthorize.html', data)

@login_required
def clients(request):
    """Show a list of clients (== tokens) belonging to the user."""
    
    # we only need the models in here, so we import them right here. In your implementation, you should import them at the top.
    from oauth_app.models import OAuthAccessToken, OAuthRequestToken
    
    data = {}
    
    data['access_tokens'] = OAuthAccessToken.objects.filter(user=request.user)
    data['request_tokens'] = OAuthRequestToken.objects.filter(user=request.user)
    
    return render(request, 'oauth/client_list.html', data)

