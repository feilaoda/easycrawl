# -*- coding: utf-8 -*-

import logging
import traceback
import json
import os
import urllib
import re
from datetime import datetime
from random import randint
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from tornado.options import options    
from easycrawl.spider import EasySpider, EasyWorker
from easycrawl.util import to_md5, merge_url, parse_media_url
from easycrawl.database import crawldb
from easycrawl.helper import update_crawl_url_status, create_crawl_class

from .parser import parse_data
from .models import EslPod

from entity.models import Entity

from dojang.database import db as to_db
from entity.models import Entity

from movie.models import Movie, MediaLink,MovieMediaLink
from search.models import  SearchMovie
from keepcd.util import file_md5

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
    

from english.models import LanguageChannel, LanguageResource
from easycrawl.database import crawldb

eslpod_title = re.compile("ESL Podcast[ \d]+")

class Spider(EasySpider):
    movie_clazz = create_crawl_class('esl_pod')

    def finished(self, db):
        pods = EslPod.query.filter_by(is_parsed=0).order_by('publish_time').all()
        c = LanguageChannel.query.filter_by(name='eslpod').first()
        if c is None:
            print "eslpod channel is None"
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
                
            title = pod.title.replace(u'–',"").replace(u'-',"").replace(u'\x92',"").replace(u'\x96',"")
            r.title = eslpod_title.sub("",title).strip()
            print r.title
            r.description = pod.content
            r.resource_url = pod.url
            r.publish_time = pod.publish_time
            to_db.session.add(r)
            to_db.session.commit()

            if pod.media:
                media_file = pod.media.split('/')[-1]
                normal_media_file = "eslpod_%d.mp3" % r.id # media_file.lower()
                #dest_orig_media_file = options.local_media_path + "/static/english/eslpod/%s" % media_file
                #dest_orig_media_url = "/static/english/eslpod/%s" % media_file
                
                dest_media_file = options.local_media_path + "/static/english/eslpod/%s" % normal_media_file
                dest_media_url = "/static/english/eslpod/%s" % normal_media_file
                
                dest_tmp_file = "/tmp/eslpod/%s" % media_file
                
                if not os.path.exists(dest_media_file):
                    try:
                        print "download pod media: %s" % pod.media, dest_media_file
                        u = urllib.FancyURLopener()
                        u.retrieve(pod.media, dest_tmp_file)
                    except IOError as e:
                        raise e
                    r.original_media = pod.media
                    
                    if not os.path.exists(dest_tmp_file):
                        print "%s not exists" % dest_tmp_file
                    else:
                        split_media_file = "split_"+media_file.lower()
                        dest_split_media_file = "/tmp/eslpod/%s" % (split_media_file)
                        fast_dialog = pod.fast_dialog
                        try:
                            m = re.findall("(\d+):(\d+)", pod.fast_dialog)
                            if len(m) >= 1 and len(m[0]) >=2:
                                minu = int(m[0][0])
                                second = int(m[0][1])
                                second -= 1
                                if second < 0:
                                    second=0
                                fast_dialog = "%d:%d" % (minu, second)
                                print fast_dialog
                            else:
                                print "not find fast_dialog" , pod.fast_dialog
                        except Exception, e:
                            print e
                            pass

                        if fast_dialog:
                            start_time = fast_dialog.replace(':', '.')

                            cmd = "mp3splt -o %s %s %s EOF-0.30" % (split_media_file.split('.')[0], dest_tmp_file, start_time)
                            try:
                                print cmd
                                os.system(cmd)
                                mv_cmd = "mv %s %s" % (dest_split_media_file, dest_media_file)
                                print mv_cmd
                                os.system(mv_cmd)
                            except Exception, e:
                                print e
                        else:
                            try:
                                mv_cmd = "mv %s %s" % (dest_tmp_file, dest_media_file)
                                print mv_cmd
                                os.system(mv_cmd)
                            except Exception, e:
                                print e
                        
                if os.path.exists(dest_media_file):
                    r.original_media = pod.media

                    if os.path.exists(dest_media_file):
                        print dest_media_file
                        media_md5 = file_md5(dest_media_file)
                        r.media = "/static/english/eslpod/%s?md5=%s" % (normal_media_file, media_md5)
                    else:
                        r.media = None
                        
                to_db.session.add(r)
                to_db.session.commit()


            pod.is_parsed = 200
            pod.resource_id = r.id
            crawldb.session.add(pod)
            crawldb.session.commit()



    def save_movie(self, db, kv):
        now_time = datetime.now()
        
        url = merge_url(kv['url'], self.data_url_prefix)
        url_hash = to_md5(url)
        eslpod = EslPod.query.filter_by(url_hash=url_hash).first()
        
        if eslpod is None:
            eslpod = EslPod()
 
        eslpod.url_hash = url_hash
        eslpod.url = url
        eslpod.title = kv['title']
        eslpod.content = kv['content']
        eslpod.media = kv['media']
        eslpod.is_parsed = 0
        eslpod.publish_time = kv['publish_time']
        eslpod.slow_dialog = kv['slow_dialog']
        eslpod.fast_dialog = kv['fast_dialog']

        db.session.add(eslpod)
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

worker = EasyWorker(crawldb, 'eslpod')





