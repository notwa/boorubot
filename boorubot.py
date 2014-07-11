#!/bin/python

import os
import os.path
import sys
import shutil
import subprocess as sp
import requests
import hashlib
from descgen import gendesc

HANDLE = 'boorubot'
IMG_DIR = 'hot'

MAX_WIDTH = 1024
MAX_HEIGHT = 2048
MAX_SIZE = 3*1024*1024

SITE = 'http://danbooru.donmai.us'
JSON = SITE+"/posts.json?tags=order:rank"
POSTS = SITE+"/posts/"

HOME = os.environ['HOME']
t = HOME+'/.gem/ruby/2.1.0/bin/t'

lament = lambda *args, **kwargs: print(*args, file=sys.stderr, **kwargs)

# subprocess still comes with the same old useless wrappers
# so we'll write our own
def poopen(args):
    p = sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE)
    out, err = p.communicate()
    return p.returncode, out, err

def dimensions(f):
    ret, dim, err = poopen(['gm', 'identify', '-format', '%wx%h\n', f])
    if ret != 0:
        raise Exception(err)
    # gifs return multiple lines
    line = str(dim, 'ascii').splitlines()[0]
    dim = line.split('x')
    return int(dim[0]), int(dim[1])

def resize(f, fout):
    newsize = '{:}x{:}'.format(MAX_WIDTH, MAX_HEIGHT)
    cmd = 'gm convert -resize '+newsize+' -quality 93'
    cmd = cmd.split(' ')
    cmd.append(f)
    cmd.append(fout)
    ret, out, err = poopen(cmd)
    if ret != 0:
        raise Exception(err)

def jpgize(f, fout, quality=80):
    cmd = 'gm convert -format jpg -quality {:2i}%'.format(quality)
    cmd = cmd.split(' ')
    cmd.append(f)
    cmd.append(fout)
    ret, out, err = poopen(cmd)
    if ret != 0:
        raise Exception(err)

def optipng(f, fout):
    shutil.copy2(f, fout)
    ret, out, err = poopen(['optipng', '-o2', fout])
    if ret != 0:
        raise Exception(err)

def tweet(text, img=None, trc=None):
    cmd = [t, 'update', text]
    if img != None:
        cmd.append('-f')
        cmd.append(img)
    if trc != None:
        cmd.append('-P')
        cmd.append(trc)
    ret, out, err = poopen(cmd)
    if ret != 0:
        raise Exception(err)

def run(args=None):
    try:
        os.mkdir(IMG_DIR)
    except FileExistsError:
        pass

    cwd = os.getcwd()
    trc = os.path.join(cwd, '.trc')
    os.chdir(IMG_DIR)

    shutil.copy2(HOME+'/.trc', trc)
    poopen([t, 'set', 'active', HANDLE, '-P', trc])

    r = requests.get(JSON)
    if r.status_code != 200:
        raise Exception('status code '+r.status_code+' for URL '+JSON)

    j = r.json()
    if type(j) != list:
        raise Exception('bad json (not a list!)')

    for post in j:
        try:
            path = post['file_url']
        except KeyError:
            continue

        _, _, fn = path.rpartition('/')
        md5, _, ext = fn.rpartition('.')

        saved = fn
        if os.path.isfile(saved):
            #print(md5+' already exists')
            continue

        r = requests.get(SITE+path)
        if r.status_code != 200:
            raise Exception('status code '+r.status_code+' for URL '+SITE+path)

        saved_md5 = hashlib.md5(r.content).hexdigest()
        if md5 != saved_md5:
            raise Exception('md5 mismatch! '+saved_md5+' should be '+md5)

        fs = len(r.content)
        with open(saved, 'bw') as f:
            f.write(r.content)

        #print('shoulda saved as '+saved)

        w, h = dimensions(saved)
        #print('{:} by {:}'.format(w, h))

        #def prepimg(fn):
        # readimg() would make struct with fmt fs w h md5 fields
        # fn .ext [fs] .w .h
        final = fn
        if ext == 'gif':
            if fs > MAX_SIZE:
                lament(fn+' is too big! skipping')
                continue
            if w > MAX_WIDTH or h > MAX_HEIGHT:
                lament(fn+' is too wide or tall! skipping')
                continue
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
                fn = 'j-'+fn
                jpgize(final, fn, quality)
                quality -= 3
            final = fn

        desc = gendesc(post)
        tweet(desc+POSTS+str(post['id']), final, trc)

        break

    os.chdir(cwd)

# TODO: delete saved file when exception occurs

if __name__ == '__main__':
    ret = 0
    try:
        ret = run(sys.argv)
    except KeyboardInterrupt:
        sys.exit(1)
    sys.exit(ret)
