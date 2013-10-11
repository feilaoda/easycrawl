from easycrawl.util import to_md5


def update_crawl_status(clazz, db, url, status):
    url_hash = to_md5(url)
    crawl_url = clazz.query.filter_by(url_hash=url_hash).first()
    if crawl_url:
        crawl_url.is_saved = status
        db.session.add(crawl_url)
        db.session.commit()