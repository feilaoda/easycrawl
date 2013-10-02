# -*- coding: utf-8 -*-

import cPickle
from dojang.util import to_md5,import_object
from urlparse import urlparse
from easycrawl.crawl import EasyCrawler

from .models import CrawlUrl, CrawlLog, ObjectDict, CrawlSite, CrawlSiteSettings

STAT_INIT = int(0)
STAT_DONE = int(200)
STAT_RUNNING = int(1)
STAT_ERROR = int(500)




def create_crawl_class(tablaname):
    name = 'crawl_%s' % tablaname
    db_dict={'__tablename__':name,
        '__table_args__':{'autoload':False, 'extend_existing':True},}

    clz = type(str(tablaname)+'CrawlUrl', (CrawlUrl,), db_dict)

    return clz



def save_crawl_data(clazz, db, item, html, save_html=False):
    #update is saved status
    crawl_url = clazz.query.filter_by(id=item.id).first()
    if crawl_url is not None:
        crawl_url.is_saved = STAT_DONE
        db.session.add(crawl_url)
        db.session.commit()
        print 'update STAT DONE url:', crawl_url.url, "is/or not data?: ", crawl_url.is_data, "save html:", save_html
        if not save_html:
            return
        else:

            crawl_url.html = cPickle.dumps(html)
            db.session.add(crawl_url)
            db.session.commit()

        # if crawl_url.is_data == 1:
        #     print 'saving data ', crawl_url.url, 
        #     url_hash = to_md5(crawl_url.url)
        #     crawl_data = CrawlData.query.filter_by(url_hash=url_hash).first()
        #     crawl_content = None
        #     if crawl_data is None:
        #         print 'crawl_data is not exist ', crawl_url.url, 
        #         crawl_data = CrawlData()
        #         crawl_data.url = crawl_url.url
        #         crawl_data.url_hash = url_hash
        #         purl = urlparse(crawl_url.url)
        #         crawl_data.domain = purl.netloc
        #     else:
        #         crawl_content = CrawlContent.query.filter_by(id=crawl_data.content_id).first()
            
           
        #     crawl_data.is_updated=1

        #     if not crawl_content:
        #         crawl_content = CrawlContent()
             
        #     print 'save html content', crawl_data.url   
        #     crawl_content.html = html
        #     crawl_content.url = crawl_url.url
        #     crawl_content.url_hash = url_hash
        #     db.session.add(crawl_content)
        #     db.session.commit()


        #     crawl_data.content_id = crawl_content.id
        #     db.session.add(crawl_data)
        #     db.session.commit()


def update_crawl_status(clazz, db, url, status):
    url_hash = to_md5(url)
    crawl_url = clazz.query.filter_by(url_hash=url_hash).first()
    if crawl_url:
        crawl_url.is_saved = status
        db.session.add(crawl_url)
        db.session.commit()

def update_crawl_url_status(clazz, db, id, status):
    crawl_url = clazz.query.filter_by(id=id).first()
    if crawl_url:
        crawl_url.is_saved = status
        db.session.add(crawl_url)
        db.session.commit()


def logger_db_error(db, site_id, log):
    log = CrawlLog()
    log.site_id = site_id
    log.log = log
    db.session.add(log)
    db.session.commit()

def load_settings(site):
    site_settings = CrawlSiteSettings.query.filter_by(site_id=site.id).all()
    settings = ObjectDict()
    settings['site_id'] = site.id
    headers=dict()
    for setting in site_settings:
        settings[setting.key] = setting.value
        if setting.key.startswith('Header-'):
            key = setting.key[7:]
            headers[key] = setting.value

    settings['headers'] = headers
    return settings