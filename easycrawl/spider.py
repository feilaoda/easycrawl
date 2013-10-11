# -*- coding: utf-8 -*-
#!/usr/bin/env python


import re
import urllib2
from urlparse import urlparse
from time import sleep
import traceback
import md5
import logging
import cPickle
from datetime import datetime
from scrapy.selector import HtmlXPathSelector


from .crawl import Executor, EasyCrawler
from .util import to_md5, merge_url

logger = logging.getLogger(__name__)


def create_request(url, headers):
    request = urllib2.Request(url)
    for k,v in headers.items():
        request.add_header(k, v)
    return request

def make_matatable(name):
    pass

def create_easycrawl_worker(db, site_name):
    return EasyWorker(db, site_name)

class Item(object):
    def __init__(self, name, patten, action):
        self.id = 0
        self.url = None
        self.is_saved = 0
        self.is_data = 0
        self.category = None
        self.code = 0
        self.html =  None
        self.rule = None

class Rule(object):
    """docstring for Rule"""
    def __init__(self, name, patten, action):
        super(Rule, self).__init__()
        self.name = name
        self.patten = patten
        self.action= action
        


class EasySpider(Executor):
    def __init__(self, settings):
        self.site_name = settings.site_name
        # self.crawl_class = create_crawl_class(settings.site_name)
        self.site_id = settings.site_id
        self.headers = settings.headers
        self.settings = settings
        if settings.data_url_prefix is None:
            self.data_url_prefix = ''
        else:
            self.data_url_prefix = settings.data_url_prefix

        if settings.crawl_url_prefix is None:
            self.crawl_url_prefix = ''
        else:
            self.crawl_url_prefix = settings.crawl_url_prefix

        if settings.debug is None or not settings.debug:
            self.debug = False
        else:
            self.debug = True

        if settings.sleep_period:
            self.sleep_period = float(settings.sleep_period)
        else:
            self.sleep_period = 0

        self.rules = settings['rules']



    # def scheduler(self):
    #     items = self.load_urls(count=30)
    #     for item in items:
    #         item.is_saved = STAT_RUNNING
    #         db.session.add(item)
    #         db.session.commit()
        
    #     return items
    
    # def load_urls(self, count=30):
    #     urls = self.crawl_class.query.filter_by(is_saved=0).limits(0, 30).all()
    #     return urls

    def check_rules(self, url):
        for rule in self.rules:
            patten = rule.patten.strip()
            if re.search(patten, url):
                return rule
        return None
    
    # def is_data_url(self, url):
    #     for patten in self.data_urls:
    #         patten = patten.strip()
    #         if re.search(patten, url):
    #             return True
    #     return False
    
    # def is_crawl_url(self, url):
    #     for patten in self.crawl_urls:
    #         patten = patten.strip()
    #         if re.search(patten, url):
    #             return True
         
    #     return False




    def worker(self, item):
        if self.sleep_period > 0:
            sleep(self.sleep_period)
        res = None
        new_urls = []
        res = self.__download_url(item.url)
        res_item = Item()
        res_item.code = res['code']
        res_item.id = item.id
        res_item.is_data = item.is_data
        res_item.url = item.url
        res_item.category = item.category
        if res_item.code == 200:
            res_item.html = res['html']
            new_urls = self.__parse_new_urls(res)
            rule = self.check_rules(item.url)
            if rule:
                res_item.rule = rule
        return res_item, new_urls

    def after_worker(self, item, newurls):
        pass

    def pipeline(self, item):
        items = dict()
        try:
            if item.rule.action != 'data':
                return None
            hxs = HtmlXPathSelector(text=item.html)
            action_name = item.rule.name
            parser = self.settings[action_name]
            if parser:
                res = parser(hxs, items)
                if not res:
                    logger.error('spider parser %s parse(hxs, items) error' % action_name)
                    return None
            else:
                logger.error('can not find parser %s' % action_name)
                return None
        except Exception, e:
            logger.error('parse pipeline error, %s' % traceback.format_exc())
            return None
        return items

    def __download_url(self, url):
        logger.debug("Download starting...[%s]\n" % url)
        request = create_request(url, self.headers)
        try:
            response = urllib2.urlopen(request, timeout=20)
            html = response.read()
            if ('Content-Encoding' in response.headers and response.headers['Content-Encoding']) or \
                    ('content-encoding' in response.headers and response.headers['content-encoding']):
                    import gzip
                    import StringIO
                    data = StringIO.StringIO(html)
                    gz = gzip.GzipFile(fileobj=data)
                    html = gz.read()
                    gz.close()

            if 'Set-Cookie' in response.headers:
                cookies = response.headers['Set-Cookie']
                self.headers['Cookie'] = cookies

            response.close()
            logger.debug("Download end...[%s]\n" % url)
            return dict(code=200, html=html)

        except urllib2.HTTPError, e:
            logger.error('you got an error with the httperror, %s' % traceback.format_exc())
            return dict(code = e.code)
        except urllib2.URLError, e:
            logger.error('you got an error with the urlerror, %s' % traceback.format_exc())
            return dict(code = 500)

        return dict(code=-1)
    
    def __parse_new_urls(self, result):
        if result['code'] != 200:
            return []
        html = result['html']
        hxs = HtmlXPathSelector(text=html)
        links = hxs.select('//a/@href').extract()
        new_urls = []
        for url in links:
            rule = self.check_rules(url)
            if rule:
                if rule.action == 'list':
                    new_urls.append([url, 'list'])
                elif rule.action == 'data':
                    new_urls.append([url, 'data'])

         
               
        return new_urls
    
    
            
    def run_parser(self):
        urls = self.crawl_class.query.filter_by(is_saved=0, is_data=1).limits(0, 30).all()
        results = []
        print "url count is", len(urls)
        for u in urls:
            item = dict()
            print u.url
            item['id'] = u.id
            item['url'] = u.url
            item['html'] = cPickle.loads(u.html)
            item['is_data'] = u.is_data
            item['category'] = u.category
            results.append(item)
        self.debug_pipeline(results)

    
