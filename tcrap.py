#!/usr/bin/env python3

from birdy import twitter
import yaml
import random
#import uuid

from retry import retry

# TODO: bird, birdy, twitter, tweet… so many similar names. rename crap.
#       also, rename tcrap.

# spoof android client headers
# props to https://github.com/Pilfer/PyTwitter/blob/master/twitter.py
# we can't actually use the X-* headers though
# because then the server expects a slightly different OAuth implementation.
# i believe it differs in how it handles the POST body;
# it probably does (not?) urlencode BEFORE signing with OAuth.
# this is evident as a purely alphanumeric tweet will pass,
# but one with even spaces will fail.
# oh well.
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
    argc = len(sys.argv)
    if argc < 2:
        print('usage:', sys.argv[0], '{account} [text [image]]')
        sys.exit(1)
    tweeter = bird(sys.argv[1])
    text = 'test tweet'
    img = None
    if argc > 2:
        text = sys.argv[2]
    if argc > 3:
        img = sys.argv[3]
    tweeter(text, img)
