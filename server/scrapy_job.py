from urllib.parse import urlparse
from twisted.internet import defer
import sys
import os
from model import Assistant
from scrapy.crawler import CrawlerRunner, CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor

# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# BASE_DIR = os.path.dirname(PROJECT_ROOT)
# print('BASE_DIR:', BASE_DIR)
# sys.path.append(os.path.join(BASE_DIR, 'crawler'))  # Add project directory to system path

from parselink.spiders.link_spider import LinkSpider
import subprocess

from build_index_search import build_documents

os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'  # Disable fork safety for macOS

def fn_hello_job(a="test"):
    print('fn_hello_job:', a)
    return a

def run_scrapy_job(start_url, assistant_id):
    runner = CrawlerRunner(get_project_settings())

    @defer.inlineCallbacks
    def crawl():
        print('run_scrapy_job:crawl:start_url:', start_url)
        yield runner.crawl(LinkSpider, start_url=start_url, assistant_id=assistant_id, max_urls=500)
        reactor.stop()

    crawl()
    reactor.run()
    return [start_url, assistant_id]

def generate_valid_name(name):
    # Remove protocols and replace invalid characters
    valid_name = name.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_')
    # Ensure the name starts and ends with an alphanumeric character
    valid_name = valid_name.strip('_')
    # Ensure the name is within the required length
    if len(valid_name) < 3:
        valid_name = valid_name.ljust(3, 'a')
    elif len(valid_name) > 63:
        valid_name = valid_name[:63]
    return valid_name

def run_scrapy_process(start_url, assistant_id):
    runner = CrawlerProcess()
    runner.crawl(LinkSpider, start_url=start_url, assistant_id=assistant_id, max_urls=500)
    runner.start()

    assistant = Assistant.get(Assistant.id == assistant_id)
    # Use the helper function to generate a valid collection name
    valid_name = generate_valid_name(assistant.name)
    print('run_scrapy_process:build_query_engine:', valid_name)
    
    build_documents(assistant.id)

    return [start_url, assistant_id]

