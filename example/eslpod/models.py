from sqlalchemy import Column
from sqlalchemy import Integer, String, DateTime, Text, Float
import time
from datetime import datetime

from easycrawl.database import crawldb


class EslPod(crawldb.Model):
    __tablename__ = 'data_esl_pod'

    id = Column(Integer, primary_key=True)
    url_hash = Column(String(100), nullable=True, index=True)
    url = Column(String(200), nullable=True, index=True)
    title = Column(String(250))
    content =  Column(Text)
    media = Column(String(250))
    slow_dialog = Column(String(50))
    fast_dialog = Column(String(50))
    publish_time = Column(DateTime, default=datetime.utcnow)
    resource_id = Column(Integer, nullable=True, index=True)
    is_parsed = Column(Integer, default=0, index=True)
    created = Column(DateTime, default=datetime.utcnow)
    
