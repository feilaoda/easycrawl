import re
from easycrawl.mysql.spider import create_crawl_class
from easycrawl.mysql.spider import MySQLSpider

def parse_eslpod(hxs, items):
    publish_time = hxs.select('//span[@class="date-header"]//text()').extract()
    if publish_time:
        items['publish_time'] = extract_value(publish_time)


    titles = hxs.select('//span[@class="pod_body"]/b[@class="pod_title"]/text()').extract()
    if titles:
        title = extract_value(titles)
        esl_cafe = title.find("English Cafe")
        if esl_cafe>0:
            print esl_cafe
            return None
        items['title'] = title

    media_urls = hxs.select('//span/a[@target="_blank"]/@href').extract()
    media_url = None
    for url in media_urls:
        print url
        if url.endswith('.mp3'):
            media_url = url
            break

    items['media'] = media_url
    # print "media", media_url
    pod_html = ""
    table_body = hxs.select('//span[@class="pod_body"]/table[@class="podcast_table_home"]')
    # print "table_body length:", len(table_body)
    if len(table_body)>=2:
        t1 = table_body[0]
        media_info =  t1.select('./tr/td/span[@class="pod_body"]').extract()
        media_info = extract_value(media_info)
        # print media_info
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
    
    pod_html = pod_html.replace(u'\x92', "'")
    items['content'] = pod_html

    return items


parsers = {
    'esl_data': parse_eslpod,
}



class EslPodHtmlParser(object):
    script_sheet = re.compile(r"<(script|style).*?>.*?(</\1>)", 
                              re.IGNORECASE | re.DOTALL)
    #HTML comments - can contain ">"
    comment = re.compile(r"<!--(.*?)-->", re.DOTALL) 
    #HTML tags: <any-text> except <b></b>
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
        text = EslPodHtmlParser.nspace.sub(" ", text)
        text = EslPodHtmlParser.retspace.sub("\n", text)
        text = EslPodHtmlParser.n2ret.sub("<br/>", text)
        text = text.strip()
        return text



class Spider(MySQLSpider):
    movie_clazz = create_crawl_class('esl_pod')

    
