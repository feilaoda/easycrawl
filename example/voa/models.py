from sqlalchemy import Column
from sqlalchemy import Integer, String, DateTime, Text, Float
import time
from datetime import datetime

from easycrawl.database import crawldb


class Voa(crawldb.Model):
    __tablename__ = 'data_voa_news'

    id = Column(Integer, primary_key=True)
    url_hash = Column(String(100), nullable=True, index=True)
    url = Column(String(200), nullable=True, index=True)
    title = Column(String(250))
    category = Column(String(50)) #special, standard
    content =  Column(Text)
    media = Column(String(250))
    publish_time = Column(DateTime, default=datetime.utcnow, index=True)
    is_parsed = Column(Integer, default=0, index=True)
    created = Column(DateTime, default=datetime.utcnow)
    
