# -*- coding: utf-8 -*-

debug = True
#address = '0.0.0.0'
sqlalchemy_engine = "mysql://root:admin@localhost:3306/mysite?charset=utf8"
easycrawl_engine = "mysql://root:admin@localhost:3306/crawl?charset=utf8"

sqlalchemy_kwargs = {
    'echo':False
}
port=7200
version="1.0"
autoescape=None
login_url = "/account/signin"
memcache = "127.0.0.1:11211"
cookie_secret = "keepcd.com 3fd0348db6303181634291f252fb9172"
password_secret = "3fd0348db6303181634291f252fb9172"
static_url_prefix = '/static/'


local_upload_path = '/Users/zhenng/Work/python/keepcd/static/upload'
local_upload_url = '/static/upload'
local_image_path = '/Users/zhenng/Work/python/keepcd/keepcd'


default_locale='zh_CN'



