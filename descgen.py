#!/bin/python

import re
from collections import OrderedDict

re_pedant = re.compile('(_\([^()]+\))+$')
restrip = lambda s: re_pedant.subn('', s)[0]
# http://stackoverflow.com/a/12681879
uniq = lambda t: [x for x in OrderedDict.fromkeys(t)]
spacelist = lambda t: [restrip(v).replace('_', ' ') for v in t.split(' ')]

not_safe = (
    'nipples',
    'suggestive fluid',
    'nude',
)

definitely_nsfw = (
    'pussy juice',
    'cum',
)

not_even_once = (
    'bestiality',
)

short = {
    'dungeon ni deai wo motomeru no wa machigatteiru darou ka': 'danmachi',
    'ano hi mita hana no namae wo bokutachi wa mada shiranai.': 'anohana',
    'to aru kagaku no railgun': '/railgun',
    #'to aru kagaku no railgun s': 'wtf is this?',
    'to aru majutsu no index': '/index',
    'to aru majutsu no index: endymion no kiseki': 'endymion no kiseki',
    'to aru majutsu no index: new testament': 'new testament',
}

shorten = lambda tags: [short[tag] if tag in short else tag for tag in tags]

def humanlist(t, n):
    hs = ''
    for i, s in enumerate(t):
        if i == 0:
            hs += s
        else:
            hs += ', ' + s
        if i >= n:
            break
    if hs == '':
        return '❓'
    if n + 1 < len(t):
        hs += '…'
    return hs

def gendesc(post):
    # the great museum heist
    rats = uniq(spacelist(post['rating']))
    arts = uniq(spacelist(post['tag_string_artist']))
    cars = uniq(spacelist(post['tag_string_character']))
    cops = uniq(spacelist(post['tag_string_copyright']))
    tags = uniq(spacelist(post['tag_string']))
    maxlen = 140 - 22 - 22 - 1 - 1 # limit - link - link - space - space
    maxtags = 5 # per art/car/cop

    fmt = '{0} ({1}) drawn by {2}'

    if 'original' in cops:
        if cars[0] == '':
            if len(cops) == 1:
                fmt = '{1} drawn by {2}'
            else:
                cars = ['original']
                cops.remove('original')
    if cops[0] == '' and cars[0] == '':
        fmt = '{1} drawn by {2}'

    if 'official art' in tags:
        if arts[0] == '':
            fmt = fmt.replace(' drawn by {2}', ' (official art)')

    rating = rats[0]
    for tag in tags:
        if rating == 's':
            if tag in not_safe:
                rating = 'q'
        if tag in definitely_nsfw:
            rating = 'e'
        if tag in not_even_once:
            return None

    if rating == 'e':
        fmt = '#nsfw ' + fmt
    elif rating == 'q':
        fmt = '#lewd ' + fmt

    arts = shorten(arts)
    cars = shorten(cars)
    cops = shorten(cops)

    # h as in human
    h_arts = []
    h_cars = []
    h_cops = [] # oxymoron
    for n in range(maxtags):
        h_arts.append(humanlist(arts, n))
        h_cars.append(humanlist(cars, n))
        h_cops.append(humanlist(cops, n))

    descs = []
    descs.append('drawn by ' + h_arts[0]) # push comes to shove
    for i in range(maxtags):
        try:
            descs.append(fmt.format(h_cars[i+0], h_cops[i+0], h_arts[i+0]))
            descs.append(fmt.format(h_cars[i+0], h_cops[i+0], h_arts[i+1]))
            descs.append(fmt.format(h_cars[i+1], h_cops[i+0], h_arts[i+1]))
        except IndexError:
            continue

    # priority to strings further into the list
    desc = ''
    for d in descs:
        if len(d) <= maxlen:
            desc = d

    if len(desc) != 0:
        desc += ' '

    return desc

if __name__ == '__main__':
    import sys
    SITE = 'http://danbooru.donmai.us'
    if len(sys.argv) > 1:
        JSON = SITE+"/posts.json?tags="+sys.argv[1]
    else:
        JSON = SITE+"/posts.json?tags=order:rank"
    import requests
    r = requests.get(JSON)
    j = r.json()
    for post in j:
        print(gendesc(post))
