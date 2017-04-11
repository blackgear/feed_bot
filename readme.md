# Feedbot

Convert partial RSS/Atom feeds into full text without pain.

## Installation

```
$ pip3 install requests lxml python-dateutil
$ mkdir .cache
```

## Usage

```
python3 bot.py
```

**ONLY** Python 3 is supported.

## Configs

```
feed_name:
  url: feed_url
  xpath: feed_xpath
  pic: default|google|weserv
```

This bot will fetch feed from `feed_url`, fetch webpage and extract content with the `feed_xpath`, then save the feed file as `feed_name.xml`.

Any Image URL will be rewrite to use google or weserv image proxy if pic set to them.

If xpath matches multi content, all of them will be process and join together.

Feed items which index larger than 10 and published longer than 1 day are removed for saving space.

## Crontab

Here is an example that refresh the feed in every 20 minutes and clean up unused caches at 00:10 everyday.

```
*/20 * * * * cd /usr/share/nginx/feed/ && python3 bot.py
0 10 * * * cd /usr/share/nginx/feed/ && find .cache -atime +1h -delete
```

## LICENSE

The MIT License

Copyright (c) 2017 Daniel

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
