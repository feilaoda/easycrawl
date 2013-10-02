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
from .helper import STAT_DONE, STAT_INIT, STAT_RUNNING
from .helper import save_crawl_data, create_crawl_class, load_settings
from .models import CrawlSite 

from .util import to_md5, merge_url
logger = logging.getLogger(__name__)

from tornado.options import options
from dojang.util import reset_option, import_object

def create_request(url, headers):
    request = urllib2.Request(url)
    for k,v in headers.items():
        request.add_header(k, v)
    return request

def make_matatable(name):
    pass

def create_easycrawl_worker(db, site_name):
    return EasyWorker(db, site_name)


class EasyWorker(object):
    def __init__(self, db, site_name):
        self.site_name = site_name
        self.db = db

    def parse(self):
        site = CrawlSite.query.filter_by(name=self.site_name).first()
        settings = load_settings(site)
        myspider = import_object("easycrawl.%s.app.Spider" % self.site_name)
        self.spider = myspider(settings)
        self.spider.run_parser()

    def debug(self):
        self.run(debug=True)


    def run(self, callback=None, worker_count=2, debug=False):
        site = CrawlSite.query.filter_by(name=self.site_name).first()
        settings = load_settings(site)
        myspider = import_object("easycrawl.%s.app.Spider" % self.site_name)
        if debug:
            settings['debug'] = True

        self.spider = myspider(settings)
        if settings.worker_count:
            worker_count = settings.worker_count
        crawler = EasyCrawler(self.spider, self.db, callback=callback,workers_count=worker_count)
        crawler.start()

    def finished(self):
        logging.debug('finished workder:')
        self.spider.finished(self.db)


class EasySpider(Executor):
    def __init__(self, settings):
        self.site_name = settings.site_name
        self.crawl_class = create_crawl_class(settings.site_name)
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
            
        if settings.data_urls is None or settings.data_urls == '':
            self.data_urls = []
        else:
            self.data_urls = settings.data_urls.split('||')

        if settings.crawl_urls is None or settings.crawl_urls == '':
            self.crawl_urls = []
        else:
            self.crawl_urls = settings.crawl_urls.split('||')

        if settings.debug is None or not settings.debug:
            self.debug = False
        else:
            self.debug = True


        if settings.sleep_period:
            self.sleep_period = float(settings.sleep_period)
        else:
            self.sleep_period = 0

        print "data_url_prefix: " , self.data_url_prefix
        print "crawl_url_prefix: " , self.crawl_url_prefix


    def scheduler(self, db):
        items = self.load_urls(count=30)
        for item in items:
            item.is_saved = STAT_RUNNING
            db.session.add(item)
            db.session.commit()
        
        return items
    
    def load_urls(self, count=30):
        urls = self.crawl_class.query.filter_by(is_saved=0).limits(0, 30).all()
        return urls
    
    def is_data_url(self, url):
        for patten in self.data_urls:
            patten = patten.strip()
            if re.search(patten, url):
                return True
        return False
    
    def is_crawl_url(self, url):
        for patten in self.crawl_urls:
            patten = patten.strip()
            if re.search(patten, url):
                return True
         
        return False

    def save_new_urls(self, db, category,  newurls):
        for url in newurls:            
            is_data = 0
            if self.is_data_url(url):
                url = merge_url(url, self.data_url_prefix)
                is_data = 1
            else:
                url = merge_url(url, self.crawl_url_prefix)

            url_hash = to_md5(url)
            old_urls = self.crawl_class.query.filter_by(url_hash=url_hash).all()
            if len(old_urls) > 0:
                continue
            new_crawl_url = self.crawl_class()
            new_crawl_url.url = url
            new_crawl_url.category = category
            new_crawl_url.url_hash = url_hash
            new_crawl_url.is_data = is_data
            
            db.session.add(new_crawl_url)
            db.session.commit()
            print "url added: ", url


    def worker(self, db, item):
        if self.sleep_period > 0:
            sleep(self.sleep_period)
        res = None
        # try:
        res = self.do_worker(item.url)
        if res['code'] == 200:
            new_urls, res = self.parse(res)
            self.save_new_urls(db, item.category, new_urls)
            save_crawl_data(self.crawl_class, db, item, res['html'], self.debug)
        else:
            code = res['code']

            crawl_url = self.crawl_class.query.filter_by(id=item.id).first()
            if crawl_url is not None:
                crawl_url.is_saved = code
                db.session.add(crawl_url)
                db.session.commit()

        res['is_data'] = item.is_data #self.is_data_url(item.url)
        res['url'] = item.url
        res['category'] = item.category
        res['url_id'] = item.id
        return res

    def do_worker(self, url):
        logger.debug("Download starting...\n[%s]" % url)
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
            logger.debug("Download end\n[%s]" % url)
            return dict(code=200, url=url, html=html)

        except urllib2.HTTPError, e:
            print 'you got an error with the http code', e
            return dict(code = e.code)
        except urllib2.URLError, e:
            print 'you got an error with the url code', e
            return dict(code = 500)

        return dict(code=-1)
    
    def parse(self, result):
        if result['code'] != 200:
            return [],[]
        html = result['html']
        hxs = HtmlXPathSelector(text=html)
        links = hxs.select('//a/@href').extract()
        new_urls = []
        for url in links:    
            
            if self.is_crawl_url(url):
                new_urls.append(url)

            if self.is_data_url(url):
                new_urls.append(url)
               
        return new_urls, result
    
    def pipeline(self, db, results):
        pass
            
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

    
