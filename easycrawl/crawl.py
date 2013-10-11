# -*- coding: utf-8 -*-
#!/usr/bin/env python

import gevent
from gevent import monkey, queue
monkey.patch_all()

from time import sleep
import traceback
import logging

logger = logging.getLogger(__name__)



class Executor(object):
    def scheduler(self):
        pass

    def after_scheduler(self, item):
        pass
    
    def worker(self, item):
        pass

    def after_worker(self, item):
        pass
    
    def pipeline(self, item):
        pass

    def after_pipeline(self, item, kv):
        pass

    def parse(hxs, items):
        pass

    def finished(self):
        pass

    def run_parser(self):
        pass
        
    def debug_pipeline(self, item):
        pass




class EasyCrawler:
    def __init__(self, executor, callback=None, timeout=1, workers_count=8, pipeline_size=100, loop_once=False):

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
        


    def start(self):
        gevent.joinall(self.jobs)

    def do_scheduler(self):
        try:
            while True:
                if self.qin.qsize()< 20:
                    items = []
                    try:
                        items = self.executor.scheduler()  #  return a generator
                        if not items:
                            self.executor.after_scheduler(items)
                    except:
                        logger.error("Pipeline error!\n%s" % traceback.format_exc()) 
                    size = 0
                    for item in items:
                        size += 1
                        self.qin.put(item)
                    logger.debug("do schedule items size is %d" % (size))
                    if size <= 0:
                        break;
                else:
                    sleep(3)

                if self.loop_once:
                    break;
                
        except Exception, e:
            logger.error("do scheduler Error!\n%s" % traceback.format_exc())
        finally:
            for i in range(self.job_count - 2):
                self.qin.put(StopIteration)
            self.job_count -= 1
            logger.debug("do scheduler done, job count: %d" % self.job_count)
            

    def do_worker(self):
        try:
            item = self.qin.get()
            while item != StopIteration:
                try:
                    res_item, new_urls = self.executor.worker(item)
                    if res_item:
                        self.executor.after_worker(res_item, new_urls)
                        self.qout.put(res_item)
                except:
                    logger.error("Worker error!\n%s" % traceback.format_exc())
                item = self.qin.get()
        finally:
            self.job_count -= 1
            logger.debug("Worker done, job count: %s" % self.job_count)

    def do_pipeline(self):
        pipeline_size = 0
        while self.job_count > 1 or not self.qout.empty():
            try:
                item = None
                try:
                    item = self.qout.get_nowait()
                    if item is not None:
                        res = self.executor.pipeline(item)
                        if res is not None:
                            self.executor.after_pipeline(item, res)

                except queue.Empty:
                    sleep(self.timeout)
            except:
                logger.error("Pipeline error!\n%s" % traceback.format_exc()) 
        
        if self.callback:
            self.callback("do pipeline size %d" % pipeline_size)



