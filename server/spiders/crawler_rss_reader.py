from fastapi import responses
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import datetime
from typing import List
from rss_spider import RssSpider
from langchain_community.document_loaders import CSVLoader
from langchain_community.retrievers import BM25Retriever
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter



# Get the current date and time
now = datetime.datetime.now()

def retrieve_rss_link(url: str):
    """Retrieve rss link from user query."""
    formatted_time = now.strftime("%Y%m%d_%H%M") + ".csv"
    
    runner = CrawlerProcess(
        settings={
            "ITEM_PIPELINES": {
                'pipelines.ValidatePipeline': 100,
                'pipelines.TransformPipeline': 200,
                'pipelines.SavePipeline': 300,
            },
            "OUTPUT_FILE": '../data_temp/rss_data/' + formatted_time,  # Đường dẫn đến file CSV
            "ELASTICSEARCH_HOST": 'http://localhost:9200',  # Địa chỉ Elasticsearch
        }
    )

    # runner = CrawlerProcess(settings)  # Truyền thiết lập vào CrawlerProcess
    runner.crawl(RssSpider, start_url=url, max_urls=500)  # Không cần output_file ở đây
    runner.start()

    full_path_csv = "../data_temp/rss_data/" + formatted_time

    return full_path_csv

retrieve_rss_link("https://thanhnien.vn/rss.html")
