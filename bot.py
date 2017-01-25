#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
import xxhash
import requests
from lxml import etree, html
from lxml.html import clean
from dateutil.parser import parse
from multiprocessing.dummy import Pool
from pathlib import Path

class FeedBot(object):
    def __init__(self):
        self.headers = {
            'Accept-Encoding': 'gzip,deflate',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
            }
        self.timeout = 10
        self.configs = {
            'embedded': False,
            'safe_attrs_only': True,
            'safe_attrs': ['src', 'href', 'height', 'width', 'alt'],
            'remove_tags': ['span', 'br', 'ins'],
        }
        self.hash = lambda x: xxhash.xxh64(x, seed=0x02).hexdigest()
        self.session = requests.Session()
        self.cleaner = clean.Cleaner(**self.configs)

    def fetch(self, url, error=[]):
        if len(error) == 3:
            return '\n'.join(error)
        else:
            print(url)
        try:
            r = self.session.get(url, headers=self.headers, timeout=self.timeout)
            return r.content.decode(r.apparent_encoding)
        except Exception as e:
            error.append('<error>fetch url: {} {}</error>'.format(url, e))
            return self.fetch(url, error=error)

    def process(self, url, xpath):
        data = self.fetch(url)
        feed = etree.fromstring(data.encode('utf-8'), etree.XMLParser(recover=True))
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'content': 'http://purl.org/rss/1.0/modules/content/',
        }

        if feed.tag == 'rss':
            content = lambda node: etree.SubElement(node, 'description')
            guid = lambda node: etree.SubElement(node, 'guid')
        else:
            content = lambda node: etree.SubElement(node, 'summary', attrib={'type':'html'})
            guid = lambda node: etree.SubElement(node, 'id')

        items = feed.xpath('//item|//atom:entry', namespaces=ns)

        for idx, node in enumerate(items):
            date = node.xpath('(pubDate|atom:published)/text()', namespaces=ns)[0]
            if idx >= 10 and time.time() - parse(date).timestamp() >= 86400:
                node.getparent().remove(node)
                continue
            for i in node.xpath('guid|description|content:encoded|atom:id|atom:summary|atom:content', namespaces=ns):
                node.remove(i)
            link = node.xpath('link/text()|atom:link/@href', namespaces=ns)[0]
            content(node).text, guid(node).text = self.extract(link, xpath)

        return etree.tostring(feed, encoding='unicode')

    def extract(self, url, xpath):
        cache = Path('.cache/{}'.format(self.hash(url)))
        try:
            if cache.exists():
                data = cache.open(encoding='utf-8').read()
            else:
                page = html.fromstring(self.fetch(url))
                node = self.cleaner.clean_html(page.xpath(xpath)[0])
                data = re.sub(r'<p>\s*</p>\n*', r'', html.tostring(node, encoding='unicode'))
                cache.open('w+', encoding='utf-8').write(data)
        except Exception as e:
            data = '<error>process page: {} {}</error>'.format(url, e)
        return etree.CDATA(data), self.hash(data)

    def wrapper(self, config):
        name, url, xpath = config
        try:
            data = self.process(url, xpath)
            open('{}.xml'.format(name), 'w+', encoding='utf-8').write(data)
        except Exception as e:
            print(url, e)

def main():
    YAML = r'(.*?):\s*$\s*url:\s*(.*?)\s*$\s*xpath:\s*(.*?)\s*$'

    feedbot = FeedBot()
    configs = re.findall(YAML, open('config.yaml', encoding='utf-8').read(), re.MULTILINE)

    pool = Pool(4)
    pool.map(feedbot.wrapper, configs)
    pool.close()
    pool.join()

if __name__ == '__main__':
    main()
