#!/bin/python

import argparse
import os, os.path
import sys
import shutil
import subprocess as sp
import requests, requests.exceptions
import hashlib
import time
from tcrap import bird
from descgen import gendesc

MAX_WIDTH = 1024
MAX_HEIGHT = 2048
MAX_SIZE = 3*1024*1024

SITE = 'http://danbooru.donmai.us'
QUERY = 'order:rank'
JSON = '/posts.json?tags='
POSTS = '/posts/'
IMG_DIR = '.'

HOME = os.environ['HOME']

lament = lambda *args, **kwargs: print(*args, file=sys.stderr, **kwargs)
printlines = lambda *args, **kwargs: print('\n'.join(args), **kwargs)

parser = argparse.ArgumentParser(description=\
  'Tweet the topmost result from a danbooru query.''')
parser.add_argument('-a', '--account', required=True, help=\
  'the twitter handle to tweet to (required)')
parser.add_argument('-q', '--query', default=QUERY, help=\
  'the query to search with (default: '+QUERY+')')
parser.add_argument('-u', '--url', default=SITE, help=\
  'which danbooru-based site to search from (default: '+SITE+')')
parser.add_argument('-o', '--outdir', default=IMG_DIR, help=\
  'the directory to store downloaded images (default: '+IMG_DIR+')')
parser.add_argument('--dummy', default=False, action='store_true', help=\
  "don't tweet; print to terminal")

class ImageLimitError(Exception):
    def __init__(self, fn, msg):
        self.fn = fn
        self.msg = msg
    def __str__(self):
        return '{}: {}'.format(self.fn, self.msg)

class StatusCodeError(Exception):
    def __init__(self, code, url):
        self.code = code
        self.url = url
    def __str__(self):
        return 'request for {} returned status code {}'.format(self.url, self.code)

class HashMismatchError(Exception):
    def __init__(self, result, desired, hashtype='md5'):
        self.a = result
        self.b = desired
        self.t = hashtype
    def __str__(self):
        return '{} mismatch between {} and desired {}'.format(self.t, self.a, self.b)

class JsonFormatError(Exception):
    pass

class PoopenError(sp.CalledProcessError):
    def __init__(self, returncode, cmd, output=None, error=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.error = error
    def __str__(self):
        s = "Command failed with exit status {}:\n{}".format(self.returncode, self.cmd)
        if self.output:
            s += "\nstdout:\n{}\n".format(self.output)
        if self.error:
            s += "\nstderr:\n{}\n".format(self.error)
        return s

def get(uri, max_retries=6):
    for i in range(max_retries):
        try:
            r = requests.get(uri)
        except requests.exceptions.ConnectionError:
            if i + 1 < max_retries:
                time.sleep(60*5)
                continue
            else:
                raise
        if r.status_code != 200:
            raise StatusCodeError(r.status_code, uri)
        return r

# subprocess still comes with the same old useless wrappers
# so we'll write our own
def poopen(args):
    p = sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise PoopenError(returncode=p.returncode, cmd=args, output=out, error=err)
    return p.returncode, out, err

def dimensions(f):
    ret, dim, err = poopen(['gm', 'identify', '-format', '%wx%h\n', f])
    # gifs return multiple lines, only the first is relevant
    line = str(dim, 'ascii').splitlines()[0]
    dim = line.split('x')
    return int(dim[0]), int(dim[1])

def resize(f, fout):
    newsize = '{}x{}'.format(MAX_WIDTH, MAX_HEIGHT)
    cmd = 'gm convert -resize '+newsize+' -quality 93'
    cmd = cmd.split(' ')
    cmd.append(f)
    cmd.append(fout)
    ret, out, err = poopen(cmd)

def jpgize(f, fout, quality=80):
    cmd = 'gm convert -format jpg -quality {}%'.format(int(quality))
    cmd = cmd.split(' ')
    cmd.append(f)
    cmd.append(fout)
    ret, out, err = poopen(cmd)

def optipng(f, fout):
    shutil.copy2(f, fout)
    ret, out, err = poopen(['optipng', '-o2', fout])

def prepimage(fn, fs):
    w, h = dimensions(fn)
    #print('{} by {}'.format(w, h))
    _, _, ext = fn.rpartition('.')

    final = fn
    if ext == 'gif':
        if fs > MAX_SIZE:
            raise ImageLimitError(final, "image filesize exceeds limit")
        if w > MAX_WIDTH or h > MAX_HEIGHT:
            raise ImageLimitError(final, "image too wide or tall")
    else:
        if w > MAX_WIDTH or h > MAX_HEIGHT:
            fn = 'r-'+fn
            resize(final, fn)
            final = fn
        if ext == 'png':
            fn = 'o-'+fn
            optipng(final, fn)
            final = fn

        quality = 90
        while os.path.getsize(fn) > MAX_SIZE:
            fn = 'j-'+fn.replace('.png', '.jpg')
            jpgize(final, fn, quality)
            quality -= 3
            if quality < 3:
                raise ImageLimitError(final, "image cannot get any worse")
        final = fn

    return final

fn = ''
def tryPost(post, site):
    try:
        path = post['file_url']
    except KeyError:
        return False, None

    global fn # gross hack for the time being
    _, _, fn = path.rpartition('/')
    md5, _, ext = fn.rpartition('.')

    if ext in ('webm', 'swf'):
        return False, None

    if os.path.isfile(fn):
        #print(fn+' already exists')
        return False, None

    r = get(site+path)
    saved_md5 = hashlib.md5(r.content).hexdigest()
    if md5 != saved_md5:
        raise HashMismatchError(saved_md5, md5)

    fs = len(r.content)
    with open(fn, 'bw') as f:
        f.write(r.content)
    #print('shoulda saved as '+fn)

    try:
        final = prepimage(fn, fs)
    except ImageLimitError as e:
        lament(str(e))
        return False, None

    return True, final

def run(args):
    a = parser.parse_args(args[1:])
    handle = a.account
    json = a.url + JSON + a.query
    posts = a.url + POSTS
    site = a.url
    outdir = a.outdir
    dummy = a.dummy
    del a

    try:
        os.mkdir(outdir)
    except FileExistsError:
        pass

    cwd = os.getcwd()
    trc = os.path.join(cwd, '.trc')
    os.chdir(outdir)

    shutil.copy2(HOME+'/.trc', trc)
    tweeter = bird(handle, trc)

    r = get(json)
    j = r.json()
    if type(j) != list:
        raise JsonFormatError('not a list')

    try:
        for post in j:
            success, final = tryPost(post, site)
            if not success:
                continue
            desc = gendesc(post)
            text = desc+posts+str(post['id'])
            f = dummy and printlines or tweeter
            f(text, final)
            break
    except:
        global fn # still gross
        if os.path.isfile(fn):
            os.rename(fn, 'fail-'+fn)
        raise
    finally:
        os.chdir(cwd)

if __name__ == '__main__':
    ret = 0
    try:
        ret = run(sys.argv)
    except KeyboardInterrupt:
        sys.exit(1)
    sys.exit(ret)
