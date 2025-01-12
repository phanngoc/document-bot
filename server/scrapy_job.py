from urllib.parse import urlparse
from twisted.internet import defer
from build_index_search import build_query_engine
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

def run_scrapy_process(start_url, assistant_id):
    runner = CrawlerProcess()
    runner.crawl(LinkSpider, start_url=start_url, assistant_id=assistant_id, max_urls=500)
    runner.start()
    return [start_url, assistant_id]

def run_scrapy_subprocess(start_url, assistant_id):
    command = [
        'scrapy', 'crawl', 'link_spider',
        '-a', f'start_url={start_url}',
        '-a', f'assistant_id={assistant_id}'
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error: {stderr.decode('utf-8')}")
    else:
        print(f"Output: {stdout.decode('utf-8')}")
    return process.returncode