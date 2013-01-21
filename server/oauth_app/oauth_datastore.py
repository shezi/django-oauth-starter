
import random
from datetime import datetime, timedelta

from django.db.models import Q

from oauth_app import oauth
from oauth_app.models import OAuthConsumer, OAuthRequestToken, OAuthAccessToken, Nonce, KEY_LENGTH, VERIFIER_LENGTH, NONCE_LENGTH


# override the following functions to change the keys, secrets and verifiers for your page
def generate_key(length=KEY_LENGTH):
    """Create a verifier for your request token."""
    return ''.join((random.choice('0123456789abcdef') for i in xrange(length)))

def generate_secret(length=KEY_LENGTH):
    """Create a verifier for your request token."""
    return ''.join((random.choice('0123456789abcdef') for i in xrange(length)))

def generate_verifier(length=VERIFIER_LENGTH):
    """Create a verifier for your request token."""
    # we exclude 0 because the user might misinterpret it as an O
    # this means that there are only 9**VERIFIER_LENGTH possible combinations
    # in our standard case, 43046721
    return ''.join((random.choice('123456789') for i in xrange(length)))
    

# example store for one of each thing
class DjangoOAuthDataStore(oauth.OAuthDataStore):

    def __init__(self):
        pass
        
        #self.consumer = oauth.OAuthConsumer('key', 'secret')
        #self.request_token = oauth.OAuthToken('requestkey', 'requestsecret')
        #self.access_token = oauth.OAuthToken('accesskey', 'accesssecret')
        #self.nonce = 'nonce'
        #self.verifier = VERIFIER

    def lookup_consumer(self, key):
        """Find the consumer that is identified by the given key."""
        try:
            consumer = OAuthConsumer.objects.get(key=key)
            return consumer
        except OAuthConsumer.DoesNotExist:
            return None

    def lookup_token(self, token_type, token_key, expired_too=False):
        """Find the token of type token_type identified by token_key.
        
        If you set expired_too=True, you'll get all tokens, even expired ones. This currently only applies to request tokens.
        """
        
        if token_type.lower() == 'request':
            try:
                if expired_too:
                    token = OAuthRequestToken.objects.get(key=token_key)
                else:
                    # we have to either check the time for expiry OR see if there's an access token (because access token present means that the user authorized the request, but the client just didn't convert to an access token yet)
                    token = OAuthRequestToken.objects.get(Q(created__gte=datetime.now() -  timedelta(minutes=10)) | Q(access_token__isnull=False), key=token_key)
                return token
            except OAuthRequestToken.DoesNotExist:
                return None
        elif token_type.lower() == 'access':
            try:
                token = OAuthAccessToken.objects.get(key=token_key)
                return token
            except OAuthAccessToken.DoesNotExist:
                return None
            
        
    def generate_nonce(self, length=NONCE_LENGTH):
        """Generate pseudorandom number for use as a nonce."""
        nonce_instance = Nonce.objects.create(nonce=''.join([str(random.randint(0, 9)) for i in range(length)]))
        return nonce_instance.nonce


    def lookup_nonce(self, oauth_consumer, oauth_token, nonce):
        """Check whether we have used the Nonce value before."""
        
        # you could store nonces keyed to consumer and token, but we just check them globally.
        
        nonce = nonce[:KEY_LENGTH]
        if Nonce.objects.filter(nonce=nonce).exists():
            return Nonce.objects.filter(nonce=nonce)[0]
        return None
        

    def fetch_request_token(self, oauth_consumer):
        """Create a request token for the given consumer with the given callback"""
        
        # TODO: check for callback value (is it consumer value automatically?)
        
        token = OAuthRequestToken.objects.create(
            consumer=oauth_consumer,
            key=generate_key(), secret=generate_secret(),
        )

        # want to check here if callback is sensible
        return token
        

    def fetch_access_token(self, oauth_consumer, oauth_token, oauth_verifier):
        """Create an access token, if the consumer, token and verifier fit together, None otherwise."""
        
        # check that there's a user and also that the status is authorized, and that we have created an access token for it
        if oauth_token.user is not None and oauth_token.status == 'authorized' and oauth_token.access_token is not None:
            return oauth_token.access_token
        
        # One of our tests failed. How sad!
        return None

    def authorize_request_token(self, oauth_token, user):
        """Authorize the request token and create an access token for it"""

        access_token = OAuthAccessToken.objects.create(
            consumer=oauth_token.consumer,
            user=user,
            key=generate_key(), secret=generate_secret(),
            status='authorized', 
        )
        
        oauth_token.user = user
        oauth_token.status = 'authorized'
        oauth_token.access_token = access_token
        oauth_token.verifier = generate_verifier()
        oauth_token.save()
        
        return oauth_token

    def deauthorize_request_token(self, token, user):
        """Deauthorized the given request token.
        
        The user is necessary to record which user denied access for this token.
        """

        token.user = user
        if token.status == 'authorized':
            token.status = 'revoked'
        elif token.status == 'waiting':
            token.status = 'declined'
        token.save()
        
        return token
        
    def deauthorize_access_token(self, token):
        """Deauthorized the given access token."""
        
        if token.status == 'authorized':
            token.status = 'revoked'
        elif token.status == 'waiting':
            token.status = 'declined'
        token.save()
        
        return token
        