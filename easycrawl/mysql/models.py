# -*- coding: utf-8 -*-
#!/usr/bin/env python
from sqlalchemy import Column
from sqlalchemy import Integer, String, DateTime, Text, Float, ForeignKey
from datetime import datetime
from .database import crawldb

StatInit = int(0)
StatDone = int(200)
StatRunning = int(1)
StatError = int(500)

class CrawlUrl(crawldb.Model):
    __abstract__ = True
    __tablename__ = 'crawl_'+ 'base'

    id = Column(Integer, primary_key=True)
    url_hash = Column(String(100), nullable=True, index=True)
    url = Column(String(200), nullable=False, index=True)
    is_saved = Column(Integer, nullable=False, default=0, index=True)
    is_data = Column(Integer, nullable=False, default=0)
    category = Column(String(200), nullable=True)
    html =  Column(Text)
    created = Column(DateTime, default=datetime.utcnow)

class CrawlSite(crawldb.Model):
    __tablename__ = 'crawl_site'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=True, index=True)
    created = Column(DateTime, default=datetime.utcnow)

class CrawlSiteSettings(crawldb.Model):
    __tablename__ = 'crawl_site_settings'
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('crawl_site.id'), index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(String(1000), nullable=True)

class CrawlLog(crawldb.Model):
    __tablename__ = 'crawl_log'
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('crawl_site.id'), index=True)
    log = Column(Text, nullable=True)
    created = Column(DateTime, default=datetime.utcnow)

