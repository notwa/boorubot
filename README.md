# boorubot

```
usage: boorubot.py [-h] -a ACCOUNT [-q QUERY] [-u URL] [-o OUTDIR] [--dummy]

Tweet the topmost result from a danbooru query.

optional arguments:
  -h, --help            show this help message and exit
  -a ACCOUNT, --account ACCOUNT
                        the twitter handle to tweet to (required)
  -q QUERY, --query QUERY
                        the query to search with (default: order:rank)
  -u URL, --url URL     which danbooru-based site to search from (default:
                        http://danbooru.donmai.us)
  -o OUTDIR, --outdir OUTDIR
                        the directory to store downloaded images (default: .)
  --dummy               don't tweet; print to terminal
```

it will not tweet (repeat) images that are already in OUTDIR.

## setup

basically…
```
pip install requests
pip install birdy
git clone https://github.com/notwa/boorubot
cd boorubot
$EDITOR .trc
./boorubot.py -a my_dumb_bot -q 'order:score rating:safe' -o safe
```

it only tweets once per execution. use cron jobs or something for periodic tweets.

## .trc files

you'll need to put a `.trc` file in the directory you're running the program from.
these are config files used by [sferik/t](https://github.com/sferik/t/)
though they can easily be written by hand. here's the basic format:

```
profiles:
  [username]:
    [consumer_key]:
      username: [username]
      consumer_key: [consumer_key]
      consumer_secret: [consumer_secret]
      token: [token]
      secret: [secret]
    [more consumer keys]:
      [etc]
  [more usernames]:
    [etc]
```

### example

```
profiles:
  my_dumb_bot:
    mCAM3nibd3eL9D7vddEn:
      username: my_dumb_bot
      consumer_key: mCAM3nibd3eL9D7vddEn
      consumer_secret: wUtdTkkwM3gXLjFtViOulTcFEYJdtNvg7oeIj4Ho0JG
      token: 1234567890-SHdORwyM7PdhPieA00NNQHxiqJPM27b8c9iRCHi
      secret: ty2KHebeteC1JKMS6MK3fH9xohpdI2THDx6hqJHi7GDMF
```
