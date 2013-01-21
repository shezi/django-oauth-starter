
import requests
from requests_oauthlib import OAuth1
import subprocess
import sys
import time

client_key = u'key'
client_secret = u'secret'

request_token_url = u'http://localhost:8000/oauth/request_token/'
authorize_url = 'http://localhost:8000/oauth/authorize/'
request_token_status_url_template = u'http://localhost:8000/oauth/request_token/%s/status/'
access_token_url =  u'http://localhost:8000/oauth/access_token/'

access_resource_url = 'http://localhost:8000/oauth/access_test_resource/'
access_resource_url_bare = 'http://localhost:8000/oauth/access_test_resource_bare/'



###########################

oauth = OAuth1(
    client_key,
    client_secret=client_secret,
#    signature_method=u'PLAINTEXT',  # standard configuration uses HMAC-SHA1 and so should you, but you need not
#    signature_type='query',  # there are three ways to add authorization information: header, body and query. standard configuration uses header, but you can choose which one you want here
)
# we are NOT providing a callback URI here, because our server will only accept pre-registered callback URIs anyway



# 1. get request token
print "-- REQUEST TOKEN"
print "getting", request_token_url
r = requests.post(url=request_token_url, auth=oauth, data={'device_name': 'testclient', 'device_type': 'linux server'})
print r.content

credentials = r.json()

request_key = credentials.get('oauth_token')
request_secret = credentials.get('oauth_token_secret')

print "got request token: key = %s, secret = %s" % (request_key, request_secret)


# 2. get authorization
print "-- AUTHORIZATION"
authorize_url = authorize_url + "?oauth_token=" + request_key
print 'Please go here and authorize,', authorize_url
# on Mac, you can do this:
subprocess.call(['open', authorize_url])

# 2. (a) Poll for status change
ok = False
request_token_status_url = request_token_status_url_template % request_key
print "checking status at", request_token_status_url
while not ok:
    status_response = requests.get(request_token_status_url)
    # print status_response.content
    status = status_response.json().get('status')
    print "polling... status is:", status
    if status == 'waiting':
        time.sleep(1)
    elif status == 'expired' or status == 'declined':
        print "did not get authorization, giving up..."
        sys.exit(1)
    elif status == 'authorized':
        ok = True

verifier = unicode(raw_input('Please enter the verifier: '))


# 3. get access token
print "-- CONVERSION"
oauth = OAuth1(client_key,
                   client_secret=client_secret,
                   resource_owner_key=request_key,
                   resource_owner_secret=request_secret,
                   verifier=verifier
                   )
print "getting access token:", access_token_url
r = requests.post(url=access_token_url, auth=oauth)
print "response:", r.content
# "oauth_token=6253282-eWudHldSbIaelX7swmsiHImEL4KinwaGloHANdrY&oauth_token_secret=2EEfA6BG3ly3sR3RjE0IBSnlQu4ZrUzPiYKmrkVU"
credentials = r.json()
print "credentials:", credentials
access_key = credentials.get('oauth_token')
access_secret = credentials.get('oauth_token_secret')


# 4. done, access resources now
print "-- ACCESS"
print "accessing resource 1"
oauth = OAuth1(client_key,
                   client_secret=client_secret,
                   resource_owner_key=access_key,
                   resource_owner_secret=access_secret)
r = requests.get(url=access_resource_url, auth=oauth)
print "content:", r.content

print "accessing resource 2"
r = requests.get(url=access_resource_url_bare, auth=oauth)
print "content:", r.content
