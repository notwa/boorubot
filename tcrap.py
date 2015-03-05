#!/bin/python
from birdy import twitter
import yaml
import random
#import uuid

from retry import retry

# TODO: bird, birdy, twitter, tweet… so many similar names. rename crap.
#       also, rename tcrap.

# this uses .trc files for my own convenience.
# if you don't have the t twitter client, you can roll your own .trc
# as such, replacing things in square brackets accordingly:
#profiles:
#  [username]:
#    [consumer_key]:
#      username: [username]
#      consumer_key: [consumer_key]
#      consumer_secret: [consumer_secret]
#      token: [token]
#      secret: [secret]
#    [more consumer keys]:
#      [etc]
#  [more usernames]:
#    [etc]

# spoof android client headers
# props to https://github.com/Pilfer/PyTwitter/blob/master/twitter.py
# we can't actually use the X-* headers though
# because then the server expects a slightly different OAuth implementation.
# i believe it differs in how it handles the POST body;
# it probably does (not?) urlencode BEFORE signing with OAuth.
# this is evident as a purely alphanumeric tweet will pass,
# but one with even spaces will fail.
# worth testing out sometime in hopes of perfect immitation.
android_headers = {
    "User-Agent": "TwitterAndroid/3.4.2 (180) sdk/8 (unknown;generic;generic;sdk;0)",
    #"X-Client-UUID": str(uuid.uuid4()),
    #"X-Twitter-Client": "TwitterAndroid",
    #"X-Twitter-Client-Version": "3.4.2",
    "Connection": "Keep-Alive"
}

class AndroidClient(twitter.UserClient):
    def configure_oauth_session(self, session):
        session.headers = android_headers
        return session

def bird(account, trc='.trc'):
    keys = getkeys(account, trc)
    t = AndroidClient(keys['consumer_key'], keys['consumer_secret'],
      keys['token'], keys['secret'])
    return lambda *args, **kwargs: tweet(t, *args, **kwargs)

def getkeys(account, trc='.trc'):
    with open(trc, 'r') as f:
        y = yaml.safe_load(f.read())
    allkeys = y['profiles'][account]
    return random.choice(list(allkeys.values()))

@retry(twitter.TwitterApiError, tries=10, wait=30)
def tweet(t, text, img=None):
    if img:
        with open(img, 'br') as f:
            t.api.statuses.update_with_media.post(status=text, media=f)
    else:
        t.api.statuses.update.post(status=text)

if __name__ == '__main__':
    import sys
    tweeter = bird('bandlimit')
    text = "here's a random image to test update_with_media"
    img = '~/Downloads/xubuntu_13_04_gpu/usr/share/glmark2/textures/terrain-grasslight-512.jpg'
    if len(sys.argv) > 1:
        text = sys.argv[1]
        img = None
    if len(sys.argv) > 2:
        img = sys.argv[2]
    tweeter(text, img)
