# -*- coding: utf-8 -*-

#!/usr/bin/python2.7
import urllib
import urllib2
from urlparse import urljoin
import MySQLdb as mdb
from time import sleep
from scrapy.selector import HtmlXPathSelector, XmlXPathSelector
import md5
import threading
import re
import string
import types
import logging

from datetime import datetime
from dateutil import parser as date_parser

from easycrawl.util import to_value, key_strip, list_join, value_strip, to_all_value
import HTMLParser
logger = logging.getLogger(__name__)


return_pattan = re.compile("\n\n+")



class VOAHtmlParser(object):
    """
    Algorithms to process HTML.
    """
    #Regular expressions to recognize different parts of HTML. 
    #Internal style sheets or JavaScript 
    script_sheet = re.compile(r"<(script|style).*?>.*?(</\1>)", 
                              re.IGNORECASE | re.DOTALL)
    #HTML comments - can contain ">"
    comment = re.compile(r"<!--(.*?)-->", re.DOTALL) 
    #HTML tags: <any-text> 除<b></b>以外
    tag = re.compile(r"<(?!(br|br/)).*?>", re.DOTALL)
    #Consecutive whitespace characters
    nwhites = re.compile(r"[\s]+")
    #<p>, <div>, <br> tags and associated closing tags
    p_div = re.compile(r"</?(p|div|br|span).*?>", 
                       re.IGNORECASE | re.DOTALL)
    #Consecutive whitespace, but no newlines
    nspace = re.compile("[^\S\n]+", re.UNICODE)
    #At least two consecutive newlines
    n2ret = re.compile("\n[ ]*\n+")
    n1ret = re.compile("\n[ ]*")
    #A return followed by a space
    retspace = re.compile("(\n )")

    #For converting HTML entities to unicode
    # html_parser = HTMLParser.HTMLParser()

    @staticmethod
    def to_nice_text(html):
        """Remove all HTML tags, but produce a nicely formatted text."""
        if html is None:
            return u""
        text = unicode(html)
        text = VOAHtmlParser.script_sheet.sub("", text)
        text = VOAHtmlParser.comment.sub("", text)
        text = VOAHtmlParser.nwhites.sub(" ", text)
        text = VOAHtmlParser.p_div.sub("\n", text) #convert <p>, <div>, <br> to "\n"
        # text = VOAHtmlParser.tag.sub("", text)     #remove all tags
        # text = HtmlTool.html_parser.unescape(text)
        #Get whitespace right
        text = VOAHtmlParser.nspace.sub(" ", text)
        text = VOAHtmlParser.retspace.sub("\n", text)
        text = VOAHtmlParser.n2ret.sub("<br><br>", text)
        text = VOAHtmlParser.n1ret.sub("<br>", text)
        text = text.strip()
        return text

def parse_voa_mp3(url):
    mp3_link = None
    request = urllib2.Request(url)
    request.add_header('Header-Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    request.add_header('Header-Accept-Charset', 'GBK,utf-8;q=0.7,*;q=0.3')
    request.add_header('Header-Accept-Language', 'zh-CN,zh;q=0.8')
    request.add_header('Header-Cache-Control', 'max-age=0')
    request.add_header('Header-Connection', 'keep-alive')
    request.add_header('Header-Host', 'learningenglish.voanews.com')
    request.add_header('Header-User-Agent', 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31')

    try:
        response = urllib2.urlopen(request, timeout=20)
        html = response.read()
        if ('Content-Encoding' in response.headers and response.headers['Content-Encoding']) or \
                ('content-encoding' in response.headers and response.headers['content-encoding']):
                import gzip
                import StringIO
                data = StringIO.StringIO(html)
                gz = gzip.GzipFile(fileobj=data)
                html = gz.read()
                gz.close()
        
        response.close()

        hxs = HtmlXPathSelector(text=html)

        li_links = hxs.select('//li[@class="downloadlinkstatic"]/a/@href').extract()
        for link in li_links:
            if link.startswith('http://'):
                mp3_link = link
                continue

        logger.debug("Download end\n[%s]" % url)
        return dict(code=200, url=url, media=mp3_link)

    except urllib2.HTTPError, e:
        print 'you got an error with the code', e
        return dict(code = e.code)
    except urllib2.URLError, e:
        print 'you got an error with the code', e
        
    return dict(code = 500)

def parse_data(item):
    html = item['html']
    print "parse0", item['url']

    html = html.decode('utf-8')#.encode('utf-8')
    html = html.replace("&rsquo;", "'")
    html = html.replace("&ldquo;", '"')
    html = html.replace("&rdquo;", '"')
    html = html.replace("&hellip;", '...')
    # html = html.replace("\<em\>", "<b>")
    # html = html.replace("\</em\>", '</b>')
    # html = html.replace('\u200b', " ")
    # print html
    hxs = HtmlXPathSelector(text=html)
    items = dict()
    items['url'] = item['url']
    items['category'] = item['category']
    print "parse", item['url']

    # tables = hxs.select('//body/table')
    # if len(tables) < 3:
    #     return None
    # td


    # print html
  
    title = hxs.select('//h1/text()').extract()
    title = to_value(title)
    
    items['title'] = title.strip()

    publish_time = hxs.select('//p[@class="article_date"]/text()').extract()
    publish_time = to_value(publish_time)
    
    publish_time = date_parser.parse(publish_time)
    items['publish_time'] = publish_time


    # print "title", title
    media_url = hxs.select('//div/ul/li[@class="listenlink"]/a/@href').extract()
    media_url = to_value(media_url)
   
    print "media", media_url
    media_url = "http://learningenglish.voanews.com"+media_url
    res = parse_voa_mp3(media_url)
    if res['code'] == 200:
        items['media'] = res['media']
    else:
        items['media'] = None

    
    html_body = hxs.select('//div[@class="zoomMe"]/*')
    pod_html = ""
    for h in html_body:
        html_piece = h.extract()
        if html_piece.startswith('<ul>') or html_piece.startswith('<div '):
            continue
        pod_html += html_piece

    pod_html = pod_html.replace("&#13;","")
    try:
        pod_html = VOAHtmlParser.to_nice_text(pod_html)
    except Exception, e:
        raise e
    items['content'] = pod_html
    # print "html", pod_html

    print items
    return items




   
