from dojang.database import SQLAlchemy
from tornado.options import options

crawldb = SQLAlchemy.create_sqlalchemy(
    options.easycrawl_engine, '__easycrawl_db'
)
