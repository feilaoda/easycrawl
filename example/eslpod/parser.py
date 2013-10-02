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
from datetime import datetime

from easycrawl.util import to_value, key_strip, list_join, value_strip
import HTMLParser


return_pattan = re.compile("\n\n+")



class EslPodHtmlParser(object):
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
    tag = re.compile(r"<(?!(b|/b)).*?>", re.DOTALL)
    #Consecutive whitespace characters
    nwhites = re.compile(r"[\s]+")
    #<p>, <div>, <br> tags and associated closing tags
    p_div = re.compile(r"</?(p|div|br|span).*?>", 
                       re.IGNORECASE | re.DOTALL)
    #Consecutive whitespace, but no newlines
    nspace = re.compile("[^\S\n]+", re.UNICODE)
    #At least two consecutive newlines
    n2ret = re.compile("\n\n+")
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
        text = EslPodHtmlParser.script_sheet.sub("", text)
        text = EslPodHtmlParser.comment.sub("", text)
        text = EslPodHtmlParser.nwhites.sub(" ", text)
        text = EslPodHtmlParser.p_div.sub("\n", text) #convert <p>, <div>, <br> to "\n"
        text = EslPodHtmlParser.tag.sub("", text)     #remove all tags
        # text = HtmlTool.html_parser.unescape(text)
        #Get whitespace right
        text = EslPodHtmlParser.nspace.sub(" ", text)
        text = EslPodHtmlParser.retspace.sub("\n", text)
        text = EslPodHtmlParser.n2ret.sub("<br/>", text)
        text = text.strip()
        return text


def parse_data(item):
    html = item['html']
    print "parse0", item['url']
    html = html.decode('iso-8859-1')
    html = html.replace(u'é',"e")
    html = html.encode('utf-8').decode('utf-8')

    
    
    
    # html = html.replace("–","-")
    hxs = HtmlXPathSelector(text=html)
    items = dict()
    items['url'] = item['url']
    print "parse", item['url']

    # tables = hxs.select('//body/table')
    # if len(tables) < 3:
    #     return None
    # td


    # print html
    publish_time = hxs.select('//span[@class="date-header"]//text()').extract()
    items['publish_time'] = to_value(publish_time)

    title = hxs.select('//span[@class="pod_body"]/b[@class="pod_title"]/text()').extract()
    print "parse1", "title"
    title = to_value(title)
    esl_cafe = title.find("English Cafe")
    if esl_cafe>0:
        print esl_cafe
        return None

    # title = title.encode('utf-8')
    # print title
    # subtitles = title.split('–')
    # if len(subtitles)>=2:
    #     title = subtitles[1]
    items['title'] = title.strip()
    # print "title", title
    media_urls = hxs.select('//span/a[@target="_blank"]/@href').extract()
    media_url = None
    for url in media_urls:
        print url
        if url.endswith('.mp3'):
            media_url = url
            break

    items['media'] = media_url
    print "media", media_url
    pod_html = ""
    table_body = hxs.select('//span[@class="pod_body"]/table[@class="podcast_table_home"]')
    print "table_body length:", len(table_body)
    if len(table_body)>=2:
        t1 = table_body[0]
        media_info =  t1.select('./tr/td/span[@class="pod_body"]').extract()
        media_info = to_value(media_info)
        print media_info
        slow_dialog = None
        fast_dialog = None
        m = re.findall("Slow[ dD]*ialog:[ ]*(\d+:\d+)", media_info)
        if len(m) >= 1:
            slow_dialog = m[0]
        else:
            m = re.findall("Slow dialogue:[ ]*(\d+:\d+)", media_info)
            if len(m) >= 1:
                slow_dialog = m[0]

        m = re.findall("Fast[ dD]*ialog:[ ]*(\d+:\d+)", media_info)
        if len(m) >= 1:
            fast_dialog = m[0]
        else:
            m = re.findall("Fast dialogue:[ ]*(\d+:\d+)", media_info)
            if len(m) >= 1:
                fast_dialog = m[0]
        items['slow_dialog'] = slow_dialog    
        items['fast_dialog'] = fast_dialog

        table = table_body[1]

        html_body =  table.select('./tr/td/span[@class="pod_body"]')
        if len(html_body) >= 1:
            body = html_body[0]
            # pod_html = body.extract()
            h = body.extract()
            if h.strip() != '':
                try:
                    pod_html = EslPodHtmlParser.to_nice_text(h)
                except Exception, e:
                    raise e
    
    # pod_html = pod_html.encode('')
    pod_html = pod_html.replace(u'\x92', "'")
    # print type(pod_html)
    items['content'] = pod_html
    # print "html", pod_html

    print items
    return items




   
