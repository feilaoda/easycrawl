# -*- coding: utf-8 -*-

import logging
import traceback
import json
import os
import urllib
from datetime import datetime
from random import randint

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from tornado.options import options    
from easycrawl.spider import EasySpider, EasyWorker
from easycrawl.util import to_md5, merge_url, parse_media_url
from easycrawl.database import crawldb
from easycrawl.helper import create_crawl_class, update_crawl_url_status

from entity.models import Entity

from dojang.database import db as to_db
from movie.models import Movie, MediaLink,MovieMediaLink
from search.models import  SearchMovie
from keepcd.util import file_md5


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
    

from english.models import LanguageChannel, LanguageResource
from easycrawl.database import crawldb

from .parser import parse_data
from .models import Voa

class Spider(EasySpider):
    movie_clazz = create_crawl_class('voa_news')

    def finished(self, db):
        pods = Voa.query.filter_by(is_parsed=0).order_by('publish_time').all()
        c = LanguageChannel.query.filter_by(name='voa special').first()
        if c is None:
            print "voa channel is None"
            return
        for pod in pods:
            #print pod.url
            r = LanguageResource.query.filter_by(channel_id=c.id, resource_url=pod.url).first()
            if r is None:
                entity = Entity()
                entity.title = pod.title
                entity.isa = "english"
                to_db.session.add(entity)
                to_db.session.commit()

                r = LanguageResource()
                r.id = entity.id
                r.channel_id = c.id
                r.study_count = 0
                r.dl_count = randint(20,40)

            if pod.media:
                r.slow_media = pod.media

                media_file = "voa_%d.mp3" % r.id
               
                dest_media_file = options.local_media_path + "/static/english/voa/%s" % media_file
                dest_media_url = "/static/english/voa/%s" % media_file
                
                dest_tmp_file = "/tmp/voa/%s" % media_file
                
                if not os.path.exists(dest_media_file):
                    try:
                        print "download pod media: %s, %s" % (pod.media, dest_tmp_file)
                        u = urllib.FancyURLopener()
                        u.retrieve(pod.media, dest_tmp_file)
                    except IOError as e:
                        raise e

                    r.original_media = pod.media
                    
                    if not os.path.exists(dest_tmp_file):
                        print "%s not exists" % dest_tmp_file
                    else:
                        try:
                            mv_cmd = "mv %s %s" % (dest_tmp_file, dest_media_file)
                            print mv_cmd
                            os.system(mv_cmd)
                        except Exception, e:
                            print e
                        

                if os.path.exists(dest_media_file):
                    print dest_media_file
                    media_md5 = file_md5(dest_media_file)
                    r.slow_media = "/static/english/voa/%s?md5=%s" % (media_file, media_md5)
                
                                
                    r.title = pod.title
                    r.description = pod.content
                    r.resource_url = pod.url
                    r.category = pod.category
                    r.publish_time = pod.publish_time
                    to_db.session.add(r)
                    to_db.session.commit()
                    
                    pod.resource_id = r.id
                    pod.is_parsed = 200
                    crawldb.session.add(pod)
                    crawldb.session.commit()



    def save_movie(self, db, kv):
        now_time = datetime.now()
        
        url = merge_url(kv['url'], self.data_url_prefix)
        url_hash = to_md5(url)
        voa = Voa.query.filter_by(url_hash=url_hash).first()
        
        if voa is None:
            voa = Voa()
 
        voa.url_hash = url_hash
        voa.url = url
        voa.title = kv['title']
        voa.content = kv['content']
        voa.media = kv['media']
        voa.category = kv['category']
        voa.is_parsed = 0
        voa.publish_time = kv['publish_time']
       
        db.session.add(voa)
        db.session.commit()
        return

    def pipeline(self, db, results):
        print "spider pipeline"
        for res in results:
            url = res['url']
            url_id = res['url_id']
            try:
                print res['url'], res['is_data']
                if res.get('is_data') and res.get('html'):
                    kv = parse_data(res)
                    if kv:
                        self.save_movie(db, kv)
                        update_crawl_url_status(self.crawl_class, db, url_id, 200)
                    else:
                        update_crawl_url_status(self.crawl_class, db, url_id, 404)
            except Exception, e:
                update_crawl_url_status(self.crawl_class, db, url_id, 500)
                logging.error(e)


    def debug_pipeline(self, results):
        print "spider debug pipeline"
        for res in results:
            kv = parse_data(res)
            print kv

worker = EasyWorker(crawldb, 'voa')





