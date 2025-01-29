import scrapy
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urlparse
import json
import csv
import html
from model import Assistant
import datetime
from elasticsearch import Elasticsearch
import feedparser
# Thêm thư viện để xử lý ngày tháng
from email.utils import parsedate_to_datetime
from typing import List, Dict
from elasticsearch_utils import index_documents_with_embeddings
# Get the current date and time
now = datetime.datetime.now()

class RssSpider(scrapy.Spider):
    name = "rss_spider"
    folder_csv = "data_temp/rss_data/"
    def __init__(self, start_url=None, max_urls=500, output_file=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else []
        self.allowed_domains = [urlparse(start_url).hostname] if start_url else []
        self.max_urls = max_urls
        self.crawled_urls = 0
        formatted_time = now.strftime("%Y%m%d_%H%M")
        if output_file is None:
            output_file = self.folder_csv + formatted_time + ".csv"
        else:
            output_file = self.folder_csv + output_file

        self.csv_file = open(output_file, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['url', 'title', 'description', 'pubDate'])
        
        # Khởi tạo kết nối Elasticsearch
        self.es = Elasticsearch("http://localhost:9200")
        
        # Danh sách để lưu các tài liệu
        self.documents = []
        self.document_count = 0  # Biến đếm số tài liệu

    def parse(self, response):
        if self.crawled_urls >= self.max_urls:
            return
        self.crawled_urls += 1
        # Check if the response contains RSS content
        feed = feedparser.parse(response.text)
        if feed.bozo == 0:  # Check if the feed is parsed correctly
            print('RSS content found')
            
            for entry in feed.entries:
                link = entry.link if 'link' in entry else 'No link'
                title = html.unescape(entry.title) if 'title' in entry else 'No title'
                description = html.unescape(entry.description) if 'description' in entry else 'No description'
                pub_date = entry.published if 'published' in entry else 'No pubDate'
                
                # Chuyển đổi pub_date sang định dạng ISO
                try:
                    if pub_date != 'No pubDate':
                        parsed_date = parsedate_to_datetime(pub_date)
                        pub_date = parsed_date.isoformat()
                except Exception as e:
                    print(f"Lỗi khi parse ngày tháng: {e}")
                    pub_date = datetime.datetime.now().isoformat()

                print('rss_url:', link, 'title:', title, 'description:', description, 'pubDate:', pub_date)
                # Save to CSV
                self.csv_writer.writerow([link, title, description, pub_date])
                
                # Lưu vào danh sách documents
                doc = {
                    'url': link,
                    'title': title,
                    'description': description,
                    'pubDate': pub_date,
                    'crawled_at': datetime.datetime.now().isoformat()
                }
                self.documents.append(doc)
                self.document_count += 1  # Tăng biến đếm

                # Kiểm tra nếu đã đủ 100 tài liệu
                if self.document_count >= 100:
                    # Lưu tất cả tài liệu vào Elasticsearch
                    try:
                        index_documents_with_embeddings(self.es, self.documents)
                        self.documents.clear()  # Xóa danh sách sau khi index
                        self.document_count = 0  # Đặt lại biến đếm
                    except Exception as e:
                        print(f"Lỗi khi lưu vào Elasticsearch: {e}")

            return

        # Extract text content and convert to Markdown format
        soup = BeautifulSoup(response.text, 'html.parser')

        rss_links = soup.find_all('a', href=lambda href: href and '.rss' in href)
        print('rss_links:', rss_links)
        for rss_link in rss_links:
            print('rss_link:', rss_link)
            if rss_link:
                rss_url = rss_link.get('href')
                yield response.follow(rss_url, callback=self.parse)
        

    def closed(self, reason):
        print('closed:reason:', reason)
        self.csv_file.close()
        
        # Lưu tất cả tài liệu còn lại vào Elasticsearch khi spider đóng
        if self.documents:
            try:
                index_documents_with_embeddings(self.es, self.documents)
            except Exception as e:
                print(f"Lỗi khi lưu vào Elasticsearch: {e}")

