# -*- coding: utf-8 -*-
#!/usr/bin/env python

import gevent
from gevent import monkey, queue
monkey.patch_all()

import re
import urllib2

from time import sleep
import traceback
import md5
import logging
from datetime import datetime
from scrapy.selector import HtmlXPathSelector
from tornado.options import options

logger = logging.getLogger(__name__)



class Executor:
    def scheduler(self, db):
        pass
    
    def worker(self, db, item):
        pass
    
    def pipeline(self, db, results):
        pass

    def after_worker(self, db, item=None):
        pass

    def finished(self, db):
        pass

    def run_parser(self):
        pass
        
    def debug_pipeline(self, results):
        pass


class EasyCrawler:
    def __init__(self, executor, db, callback=None, timeout=5, workers_count=8, pipeline_size=100, loop_once=False):

        self.executor = executor
        self.timeout = timeout
        self.loop_once = loop_once
        self.callback = callback
        self.qin = queue.Queue(0)
        self.qout = queue.Queue(pipeline_size)
        self.jobs = [gevent.spawn(self.do_scheduler)]
        self.jobs += [gevent.spawn(self.do_worker) for i in range(workers_count)]
        self.jobs += [gevent.spawn(self.do_pipeline)]
        self.job_count = len(self.jobs)
        self.db = db

        

    def start(self):
        gevent.joinall(self.jobs)

    def do_scheduler(self):
        try:
            retry_count=0
            while True:
                if self.qin.qsize()< 20:
                    items = []
                    try:
                        items = self.executor.scheduler(self.db)  #  return a generator
                    except:
                        logger.error("Pipeline error!\n%s" % traceback.format_exc()) 

                    print "do scheduler items size: ", len(items)
                    size = 0
                    for item in items:
                        size += 1
                        self.qin.put(item)
                    print "do schedule size, ", size, retry_count
                    if size <= 0:
                        break;

                    #     if retry_count >= 1:                        
                    #         break;
                    #     else:
                    #         retry_count += 1
                    #         sleep(1)
                    # else:
                    #     retry_count = 0
                else:
                    sleep(3)

                if self.loop_once:
                    break;
                
        except Exception, e:
            logger.error("Scheduler Error!\n%s" % traceback.format_exc())
        finally:
            
            for i in range(self.job_count - 2):
                self.qin.put(StopIteration)
            self.job_count -= 1
            logger.debug("Scheduler done, job count: %s" % self.job_count)
            

    def do_worker(self):

        try:
            item = self.qin.get()
            while item != StopIteration:
                try:
                    r = self.executor.worker(self.db, item)
                    self.executor.after_worker(self.db, r)
                    if r != None:
                        self.qout.put(r)
                except:
                    logger.error("Worker error!\n%s" % traceback.format_exc())
                item = self.qin.get()
        finally:
            self.job_count -= 1
            logger.debug("Worker done, job count: %s" % self.job_count)

    def do_pipeline(self):
        pipeline_size = 0
        while self.job_count > 1 or not self.qout.empty():
            sleep(self.timeout)
            try:
                results = []
                try:
                    i=0
                    while i<2:
                        i+=1
                        pipeline_size += 1
                        results.append(self.qout.get_nowait())
                        
                    if len(results) > 0:
                        self.executor.pipeline(self.db,results)
                except queue.Empty:
                    if len(results) > 0:
                        self.executor.pipeline(self.db,results)
            except:
                logger.error("Pipeline error!\n%s" % traceback.format_exc()) 
        
        if self.callback:
            self.callback("do pipeline size %d" % pipeline_size)



