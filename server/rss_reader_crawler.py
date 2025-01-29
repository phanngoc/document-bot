from fastapi import responses
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from scrapy.crawler import CrawlerProcess
import datetime
from typing import List
from spiders.rss_spider import RssSpider
from langchain_community.document_loaders import CSVLoader
from langchain_community.retrievers import BM25Retriever
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)
import streamlit as st

model = ChatOpenAI(model="gpt-4o")
memory = MemorySaver()

# Get the current date and time
now = datetime.datetime.now()

def retrieve_rss_link(url: str):
    """Retrieve rss link from user query."""
    formatted_time = now.strftime("%Y%m%d_%H%M") + ".csv"
    runner = CrawlerProcess()
    runner.crawl(RssSpider, start_url=url, output_file=formatted_time, max_urls=500)
    runner.start()

    full_path_csv = "data_temp/rss_data/" + formatted_time

    return full_path_csv

retrieve_rss_link("https://thanhnien.vn/rss.html")
