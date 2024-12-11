import streamlit as st
from urllib.parse import urlparse
from twisted.internet import defer
from build_index_search import build_query_engine
from crawler.parselink.spiders.link_spider import LinkSpider
from model import Assistant
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor
from scrapy.settings import Settings

def run_scrapy_job(start_url, assistant_id):
    runner = CrawlerRunner(get_project_settings())

    @defer.inlineCallbacks
    def crawl():
        yield runner.crawl(LinkSpider, start_url=start_url, assistant_id=assistant_id, max_urls=500)
        reactor.stop()

    crawl()
    reactor.run()
    return [start_url, assistant_id]
