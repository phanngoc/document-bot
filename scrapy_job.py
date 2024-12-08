import streamlit as st
import sys
import os
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
        yield runner.crawl(LinkSpider, start_url=start_url, assistant_id=assistant_id)
        reactor.stop()

    crawl()
    reactor.run()
    return [start_url, assistant_id]

# @defer.inlineCallbacks
# def run_scrapy_job(start_url, assistant_id):
#     settings = Settings()
#     settings.setmodule('crawler.parselink.settings')

#     runner = CrawlerRunner(settings)
#     yield runner.crawl(LinkSpider, start_url=start_url, assistant_id=assistant_id)
#     reactor.stop()

    # progress_bar = st.progress(0)
    # print('Scrapy job started...', start_url)
    # sys.path.append(os.path.abspath('crawler'))  # Add the crawler directory to the path
    # print('Scrapy job completed successfully!')
    # global query_engine
    # st.info("Building index...")
    # progress_bar.progress(50)
    
    # Extract a valid collection name from the URL
    # parsed_url = urlparse(start_url)
    # collection_name = parsed_url.hostname.replace('.', '_')
    
    # query_engine = build_query_engine(collection_name, is_builded=True)
    # st.success("Scrapy job and query engine build completed successfully!")

    # Update progress bar
    # progress_bar.progress(100)

    # Append the new assistant to the options
    # assistant_options.append(assistant.name)
    # st.experimental_rerun()
