import logging
logger = logging.getLogger(__name__)

from easycrawl.util import import_object
from easycrawl.crawl import EasyCrawler

class EasyWorker(object):
    def __init__(self, settings):
        self.site_name = settings.site_name
        myspider = import_object("%s.spider.Spider" % self.site_name)
        self.spider = myspider(settings)

    def parse(self):
        self.spider.run_parser()

    def debug(self):
        self.run(debug=True)


    def run(self, callback=None, worker_count=2, debug=False):
        if debug:
            self.spider.settings['debug'] = True

        crawler = EasyCrawler(self.spider, callback=callback, workers_count=worker_count)
        crawler.start()

    def finished(self):
        logger.debug('finished workder:')
        self.spider.finished()
