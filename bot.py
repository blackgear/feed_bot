#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
import xxhash
import requests
from lxml import etree, html
from lxml.html import clean
from dateutil.parser import parse
from urllib.parse import urljoin
from pathlib import Path
from multiprocessing.dummy import Pool

class FeedBot(object):
    def __init__(self):
        self.headers = {
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN;q=1.0,*;q=0.5',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
            }
        self.configs = {
            'embedded': False,
            'safe_attrs_only': True,
            'safe_attrs': ['src', 'href', 'height', 'width', 'alt'],
            'remove_tags': ['span'],
            }
        self.pattern = re.compile('['
            u'\U0001F600-\U0001F64F'
            u'\U0001F300-\U0001F5FF'
            u'\U0001F680-\U0001F6FF'
            u'\U0001F1E0-\U0001F1FF'
            ']+', flags=re.UNICODE)

        self.mask = 'https://images{}-focus-opensocial.googleusercontent.com/gadgets/proxy?url={}&container=focus'
        self.hash = lambda x: xxhash.xxh64(x, seed=0x04).hexdigest()
        self.session = requests.Session()
        self.cleaner = clean.Cleaner(**self.configs)

    def text(self, r):
        encoding = r.encoding
        if encoding in [None, 'ISO-8859-1']:
            encodings = requests.utils.get_encodings_from_content(r.text)
            if encodings:
                encoding = encodings[0]
            else:
                encoding = r.apparent_encoding
        return self.pattern.sub('', r.content.decode(encoding))

    def fetch(self, url, tries=1):
        if tries > 3:
            raise Exception
        else:
            print(url)
        try:
            r = self.session.get(url, headers=self.headers, timeout=tries*20)
            return self.text(r).encode('utf-8')
        except:
            return self.fetch(url, tries=tries+1)

    def extract(self, url, xpath):
        cache = Path('.cache/{}'.format(self.hash(url)))
        if cache.exists():
            data = cache.open(encoding='utf-8').read()
        else:
            parser = html.HTMLParser(encoding='utf-8', remove_comments=True, remove_blank_text=True)
            page = html.fromstring(self.fetch(url), parser=parser)

            for idx, (elem, attr, link, pos) in enumerate(page.iterlinks()):
                if elem.tag == 'img':
                    elem.set('src', self.mask.format(idx % 2, urljoin(url, link)))

            node = map(self.cleaner.clean_html, page.xpath(xpath))
            data = ''.join(map(lambda x: html.tostring(x, encoding='unicode'), node))
            cache.open('w+', encoding='utf-8').write(data)
        return etree.CDATA(data), self.hash(data)

    def process(self, config):
        name, url, xpath = config
        parser = etree.XMLParser(encoding='utf-8', recover=True, remove_comments=True, remove_blank_text=True)
        feed = etree.fromstring(self.fetch(url), parser=parser)
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
            pubdate = node.xpath('(pubDate|atom:published)/text()', namespaces=ns)
            timeout = time.time() - parse(pubdate[0]).timestamp() >= 86400 if pubdate else True
            if idx >= 10 and timeout:
                node.getparent().remove(node)
                continue
            for i in node.xpath('guid|description|content:encoded|atom:id|atom:summary|atom:content', namespaces=ns):
                node.remove(i)
            link = node.xpath('link/text()|atom:link[@rel="alternate"]/@href', namespaces=ns)[0]
            link = urljoin(url, link)
            content(node).text, guid(node).text = self.extract(link, xpath)

        data = etree.tostring(feed, encoding='unicode')
        open('{}.xml'.format(name), 'w+', encoding='utf-8').write(data)

def main():
    YAML = r'^(.*?):\s*$\s*url:\s*(.*?)\s*$\s*xpath:\s*(.*?)\s*$'

    feedbot = FeedBot()
    configs = re.findall(YAML, open('config.yaml', encoding='utf-8').read(), re.MULTILINE)

    pool = Pool(8)
    pool.map(feedbot.process, configs)
    pool.close()
    pool.join()

if __name__ == '__main__':
    main()
