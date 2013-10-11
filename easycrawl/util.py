# -*- coding: utf-8 -*-
#!/usr/bin/env python

from __future__ import with_statement
import os
import sys
import pkgutil
import md5
import urllib
import re
import types
from options import define
import HTMLParser

# def set_default_option(name, default=None, **kwargs):
#     if name in options:
#         return
#     define(name, default, **kwargs)


# def reset_option(name, default=None, **kwargs):
#     if name in options:
#         options[name].set(default)
#         return
#     define(name, default, **kwargs)

def load_settings(settings):
    headers=dict()
    for k in settings.keys():
        if k.startswith('Header_'):
            key = k[7:].replace('_','-')
            headers[key] = settings[k]
            del settings[k]
        if k.startswith('easycrawl_'):
            define(k, settings[k])

    settings['headers'] = headers
    site_name = settings['site_name']
    rules_name = "%s.rules.rules" % site_name
    rules = import_object(rules_name)
    settings['rules'] = rules
    parsers_name = "%s.spider.parsers" % site_name
    parsers = import_object(parsers_name)
    settings['parsers'] = parsers


def parse_config_file(settings, path):
    config = {}
    execfile(path, config, config)
    for name in config:
        settings[name] = config[name]
    
        

def extract_value(v):
    if v and isinstance(v, list):
        return v[0].strip()
    else:
        return None

def to_all_value(v):
    if len(v) > 0:
        return "\n".join(v)
    else:
        return ''
def all_value(v):
    if len(v) > 0:
        return " ".join(v)
    else:
        return ''

def to_value(v):
    if len(v) > 0:
        return v[0]
    else:
        return ''

def key_strip(key):
    text = key.replace(":", "").replace("\n","")
    # text = return_pattan.sub("", text)
    return text

def list_strip(lst):
    r = []
    for s in lst:
        v = s.strip()
        if v == '' or v == '\r\n\t':
            continue
        v = v.replace("&nbsp", "")
        v = v.replace(":", "")
        v = v.replace("\t", "")
        v = v.replace('\'', '\\\'')
        v = v.strip()
        r.append(v)
    return r

def list_join(lst, s):
    r = list_strip(lst)
    return s.join(r)

def value_strip(value):
    if type(value) is types.ListType:
        return list_join(value, "") #join_list(value)
    return value


class HtmlTool(object):
    """
    Algorithms to process HTML.
    """
    #Regular expressions to recognize different parts of HTML. 
    #Internal style sheets or JavaScript 
    script_sheet = re.compile(r"<(script|style).*?>.*?(</\1>)", 
                              re.IGNORECASE | re.DOTALL)
    #HTML comments - can contain ">"
    comment = re.compile(r"<!--(.*?)-->", re.DOTALL) 
    #HTML tags: <any-text>
    tag = re.compile(r"<.*?>", re.DOTALL)
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
    html_parser = HTMLParser.HTMLParser()

    @staticmethod
    def to_nice_text(html):
        """Remove all HTML tags, but produce a nicely formatted text."""
        if html is None:
            return u""
        text = unicode(html)
        # text = HtmlTool.script_sheet.sub("", text)
        # text = HtmlTool.comment.sub("", text)
        text = HtmlTool.nwhites.sub(" ", text)
        text = HtmlTool.p_div.sub("\n", text) #convert <p>, <div>, <br> to "\n"
        text = HtmlTool.tag.sub("", text)     #remove all tags
        # text = HtmlTool.html_parser.unescape(text)
        #Get whitespace right
        text = HtmlTool.nspace.sub(" ", text)
        text = HtmlTool.retspace.sub("\n", text)
        text = HtmlTool.n2ret.sub("\n\n", text)
        text = text.strip()
        return text


def import_object(name, arg=None):
    """
    .. attention:: you should not use this function
    """

    if '.' not in name:
        return __import__(name)
    parts = name.split('.')
    #try:
    obj = __import__('.'.join(parts[:-1]), None, None, [parts[-1]], 0)
    #except ImportError:
    #    obj = None
    return getattr(obj, parts[-1], arg)


def get_root_path(import_name):
    """Returns the path to a package or cwd if that cannot be found.  This
    returns the path of a package or the folder that contains a module.

    Not to be confused with the package path returned by :func:`find_package`.
    """
    loader = pkgutil.get_loader(import_name)
    if loader is None or import_name == '__main__':
        # import name is not found, or interactive/main module
        return os.getcwd()
    # For .egg, zipimporter does not have get_filename until Python 2.7.
    if hasattr(loader, 'get_filename'):
        filepath = loader.get_filename(import_name)
    else:
        # Fall back to imports.
        __import__(import_name)
        filepath = sys.modules[import_name].__file__
    # filepath is import_name.py for a module, or __init__.py for a package.
    return os.path.dirname(os.path.abspath(filepath))




def to_md5(url):
    m = md5.new()
    m.update(url)
    url_md5 = m.hexdigest()
    return url_md5 

def merge_url(url, prefix):
    if prefix == "" or prefix is None:
        return url
    if url.startswith(prefix):
        return url
    if url.startswith('./'):
        url = url[2:]
    if url[0] != '/':
        url = '/' + url
    return prefix + url

import os, errno

def mkdir_p(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise


def download_image(url, filename):
    image = urllib.URLopener()
    image.retrieve(url, filename)


def save_image(body, filename, callback=None):
        file_time = datetime.now().strftime('%Y%m')
        file_dir = options.local_static_path+'/'+file_time
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        path = os.path.join(file_dir, filename)
        
        tf = tempfile.NamedTemporaryFile()
        tf.write(body)
        tf.seek(0)

        img = Image.open(tf.name)
        img.thumbnail((1024,1024),resample=1)
                
        img.save(path)
        tf.close()

        #f = open(path, 'w')
        #f.write(body)
        #f.close()
        if not callback:
            return
        callback(os.path.join(options.local_static_url+'/'+file_time, filename))
        return


def parse_media_url(link_url):
    params = dict()
    category=''
    title=''
    size = 0
    hashes=dict()
    params['website'] = ''
    if link_url.startswith('ed2k://'):
        category, title, size, hashes = parse_ed2k_url(link_url)
    elif link_url.startswith('magnet:?'):
        category, title, hashes = parse_magnet_url(link_url)
    elif link_url.startswith('thunder'):
        category, title, hashes = parse_thunder_url(link_url)
    elif link_url.startswith('http://'):
        category, title, hashes = parse_http_url(link_url)
        params['website'] = ''
    else:
        magnet_params = link_url.split('|')
        print magnet_params,len(magnet_params), len(magnet_params[0])
        if len(magnet_params) == 2 and len(magnet_params[0]) >= 32:
            hashes['btih'] = magnet_params[0]
            title = magnet_params[1]
            category = 'magnet'
            link_url = 'magnet:?xt=urn:btih:%s' % (magnet_params[0])

    return category, title, size, hashes




def parse_thunder_url(thunder_url):
        category = 'thunder'
        title = ''
        hashes = {}
        return category, title, hashes


def parse_ed2k_url(ed2k_url):
    category = 'ed2k'
    params = ed2k_url.split('|')
    hashes = dict()
    size = None
    if len(params)>= 3:
        title = params[2]
    if len(params) >=5:
        if params[1] == 'file':
            size = params[3]
            hash_value = params[4]
            try:
                size = float(size)
                if size>1024*1024*1024:
                    size = size/(1024*1024*1024) 
                    print size
                    size = "%0.1f G" % (size)
                else:
                    size = size/(1024*1024)
                    print size
                    size = "%0.1f M" % size
            except Exception, e:
                size = None
            
            hashes['ed2k'] = hash_value

    else:
        title = ''
    
    return category,title,size,hashes

def parse_magnet_url(link_url):
    category = 'magnet'
    title = ''
    hashes = dict()
    if link_url.startswith('magnet:?'):
        uri_params = link_url[8:]
        uri_params = link_url[8:].split('&')
        params = dict()
        for param in uri_params:
            kv = param.split('=')
            if len(kv) == 2:
                k = kv[0]
                v = kv[1]
                params[k] = v
        for k in params.keys():
            v = params.get(k)
            if k == 'dn':
                title = v
            elif k == 'xt' or k.startswith('xt.'):
                v_params = v.split(':')
                if len(v_params) == 3:
                    hash_type = v_params[1]
                    hash_value = v_params[2]
                    hashes[hash_type] = hash_value

    return category, title, hashes

def parse_http_url(link_url):
    return 'http', link_url, {'md5': to_md5(link_url)}

