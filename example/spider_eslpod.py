# -*- coding: utf-8 -*-
#!/usr/bin/env python

import argparse
import os
import sys
import urllib2
import re
import json
import urllib

PROJDIR = os.path.abspath(os.path.dirname(__file__))
print "PROJDIR:", PROJDIR
ROOTDIR = os.path.split(PROJDIR)[0]
try:
    import easycrawl
    print('Start easycrawl version: %s' % easycrawl.__version__)
except ImportError:
    import site
    site.addsitedir(ROOTDIR)
    site.addsitedir(ROOTDIR+"/easycrawl")
    print('Development of easycrawl: ' + ROOTDIR)

from easycrawl.util import parse_config_file, load_settings
from easycrawl.options import ObjectDict



def run_command(settings):
    
    from easycrawl.mysql.helper import update_crawl_status
    from easycrawl.mysql.database import crawldb
    from easycrawl.mysql.worker import EasyWorker
    from easycrawl.mysql.spider import create_crawl_class
    # from keepcd.admin.easycrawl.douban.app import worker
    
    worker_name = "%s.app.worker" % settings['site_name']
    print worker_name
    worker = EasyWorker(settings)
    # worker = import_object(worker_name)
    clz = create_crawl_class('esl_pod')
    url = 'http://www.eslpod.com/website/show_all.php?cat_id=-59456'
    update_crawl_status(clz, crawldb, url, 0)
    worker.run(callback=None)
    worker.finished()

def run(site_name):
    settings = ObjectDict()
    
    parse_config_file(settings, site_name +"/settings.py")
   
    load_settings(settings)
    for k in settings.keys():
        print k,"====",settings[k]
    run_command(settings)


if __name__ == "__main__":
    site_name = "eslpod"

    # reload(sys)
    # sys.setdefaultencoding('utf8') 
    parser = argparse.ArgumentParser(
        prog='',
        description='easycrawl',
    )
    parser.add_argument('command', nargs="*")
    args = parser.parse_args()
    run(site_name)



