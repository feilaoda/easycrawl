from easycrawl.spider import Item, EasySpider
from .models import StatInit, StatRunning
from .models import CrawlUrl
from .database import crawldb

def create_crawl_class(tablaname):
    name = 'crawl_%s' % tablaname
    db_dict={'__tablename__':name,
        '__table_args__':{'autoload':False, 'extend_existing':True},}
    clz = type(str(tablaname)+'CrawlUrl', (CrawlUrl,), db_dict)

    return clz

class ClassName(object):
    """docstring for ClassName"""
    def __init__(self, arg):
        super(ClassName, self).__init__()
        self.arg = arg
        

class MySQLSpider(EasySpider):
    def __init__(self, settings):
        self.crawl_class = create_crawl_class(settings.site_name)
        self.db = crawldb
        super(MySQLSpider, self).__init__(settings)


    def load_urls(self, count=30):
        urls = self.crawl_class.query.filter_by(is_saved=StatInit).limits(0, count).all()
        return urls

    def scheduler(self):
        urls = self.load_urls(count=30)
        items = []
        for url in urls:
            item = Item()
            item.id = url.id
            item.url = url.url
            item.category = url.category
            item.is_saved = url.is_saved
            item.is_data = url.is_data
            items.append(item)
        return items

    def after_scheduler(self, items):
        for item in items:
            item.is_saved = StatRunning
            self.db.session.add(item)
            self.db.session.commit()

    def after_worker(self, item, newurls):
        if item.code == 200:
            self.save_new_urls(item.category, newurls)
            self.save_crawl_data(item, self.debug)
        else:
            crawl_url = self.crawl_class.query.filter_by(id=item.id).first()
            if crawl_url is not None:
                crawl_url.is_saved = item.code
                self.db.session.add(crawl_url)
                self.db.session.commit()

    def after_pipeline(self, item, kv):
        if res:
            self.save(item, kv)
            self.update_url_status(item.id, 200)
        else:
            self.update_url_status(item.id, 500)

    def save_new_urls(self, category,  newurls):
        for url,action in newurls:            
            is_data = 0
            if action == 'data':
                url = merge_url(url, self.data_url_prefix)
                is_data = 1
            elif action == 'list':
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
            
            self.db.session.add(new_crawl_url)
            self.db.session.commit()
            logger.debug("new url added: %s" % url)


    def save_crawl_data(self, item, save_html=False):
        crawl_url = self.crawl_class.query.filter_by(id=item.id).first()
        if crawl_url is not None:
            crawl_url.is_saved = StatDone
            if save_html and item.html:
                crawl_url.html = cPickle.dumps(item.html)
            self.db.session.add(crawl_url)
            self.db.session.commit()
            logger.debug('update url %s is saved (StatDone) , is data(%d) ? save html(%d)?'%(crawl_url.url, crawl_url.is_data, save_html))

    
    def update_url_status(self, id, status):
        crawl_url = self.crawl_class.query.filter_by(id=id).first()
        if crawl_url:
            crawl_url.is_saved = status
            self.db.session.add(crawl_url)
            self.db.session.commit()