"""
API models: Only such models that are important for the API and for the background processes.


Copyright 2013 Johannes Spielmann
Partially based on work: Copyright (c) 2007 Leah Culver (used under MIT license)
"""

import random
from django.db import models
from django.contrib.auth.models import User

KEY_LENGTH = 32
VERIFIER_LENGTH = 8
NONCE_LENGTH = 8

class OAuthConsumer(models.Model):
    """Consumer of OAuth authentication.

    OAuthConsumer is a data type that represents the identity of the Consumer
    via its shared secret with the Service Provider.

    Additionally, we store the user that created this consumer for information later.
    """
    key = models.CharField(max_length=KEY_LENGTH)
    secret = models.CharField(max_length=KEY_LENGTH)
    user = models.ForeignKey(User)

    callback = models.URLField()
    callback_confirmed = True

    class Meta:
        verbose_name = 'OAuthConsumer'
        verbose_name_plural = 'OAuthConsumers'

class CommonToken(models.Model):
    """OAuthToken is a data type that represents an End User via either an access
    or request token.
    
    key -- the token
    secret -- the token secret
    
    Additionally, we need some data for our Django integration:
    user - the user that this token is associated with
    """

    STATUS_CHOICES = (
        ('waiting', 'Waiting for authorization'),
        ('authorized', 'Authorized by user'),
        ('declined', 'Authorization was declined by user'),
        ('revoked', 'Authorization was revoked by user'),
        ('expired', 'Request token expired'), 
    )

    created = models.DateTimeField(auto_now_add=True)

    consumer = models.ForeignKey(OAuthConsumer)
    key = models.CharField(max_length=KEY_LENGTH)
    secret = models.CharField(max_length=KEY_LENGTH)

    user = models.ForeignKey(User, null=True, blank=True)

    # add additional information here
    # e.g. the device name or something like that
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    
    def set_callback(self, callback):
        """Record a callback value from the request and assume it is confirmed."""
        self.callback = callback
        self.callback_confirmed = True

    def set_verifier(self, verifier=None):
        if verifier is not None:
            self.verifier = verifier
        else:
            self.verifier = ''.join([str(random.randint(0, 9)) for i in range(VERIFIER_LENGTH)])

    def get_callback_url(self):
        if self.callback and self.verifier:
            # Append the oauth_verifier.
            parts = urlparse.urlparse(self.callback)
            scheme, netloc, path, params, query, fragment = parts[:6]
            if query:
                query = '%s&oauth_verifier=%s' % (query, self.verifier)
            else:
                query = 'oauth_verifier=%s' % self.verifier
            return urlparse.urlunparse((scheme, netloc, path, params,
                query, fragment))
        return self.callback

    def to_dict(self):
        data = {
            'oauth_token': self.key,
            'oauth_token_secret': self.secret,
        }
        return data

    def __unicode__(self):
        return u"Token(%s for user %s)" % (self.key, self.user)

    class Meta:
        abstract = True
        ordering = '-created',
        verbose_name = 'OAuthToken'
        verbose_name_plural = 'OAuthTokens'
    
class OAuthAccessToken(CommonToken):
    """The access token is an authorized token that can be used to grant access
    to the resources to a client.
    """
    class Meta:
        verbose_name = 'OAuth Access Token'
        verbose_name_plural = 'OAuth Access Tokens'

class OAuthRequestToken(CommonToken):
    """Request tokens are unauthorized requests for access tokens."""

    access_token = models.OneToOneField(OAuthAccessToken, null=True, blank=True)
    # used for looking up the access token when the client requests it

    class Meta:
        verbose_name = 'OAuth Request Token'
        verbose_name_plural = 'OAuth Request Tokens'


class Nonce(models.Model):
    """Nonce values that have been used, kept for a bit of security (to guard against nonce-fixation).
    
    You can accumulate nonce values very quickly, so you should take care to clean them up regularly.
    """
    nonce = models.CharField(max_length=NONCE_LENGTH)
    
