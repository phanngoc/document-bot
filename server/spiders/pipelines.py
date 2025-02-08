# pipelines.py
import scrapy
import csv
from elasticsearch import Elasticsearch
from datetime import datetime
from elasticsearch_utils import index_documents_with_embeddings
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

class ValidatePipeline:
    def process_item(self, item, spider):
        # Perform validation
        if 'url' not in item:
            raise scrapy.exceptions.DropItem("Missing URL in %s" % item)
        return item

class TransformPipeline:
    def process_item(self, item, spider):
        # Transform the item (e.g., clean or modify fields)
        item['url'] = item['url'].lower()
        return item

class CSVSavePipeline:
    def __init__(self, output_file):
        self.output_file = output_file
        self.existing_urls = set()  # Tập hợp để lưu trữ các URL đã tồn tại

        # Mở file CSV để ghi
        self.csv_file = open(self.output_file, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['url', 'title', 'description', 'pubDate'])

    @classmethod
    def from_crawler(cls, crawler):
        output_file = crawler.settings.get('OUTPUT_FILE', 'output.csv')
        return cls(output_file)

    def process_item(self, item, spider):
        # Kiểm tra nếu URL đã tồn tại
        if item['url'] in self.existing_urls:
            spider.logger.info(f"URL đã tồn tại: {item['url']}")
            return item

        # Thêm URL vào tập hợp
        self.existing_urls.add(item['url'])

        # Lưu vào CSV
        self.csv_writer.writerow([item['url'], item['title'], item['description'], item['pubDate']])
        return item

    def close_spider(self, spider):
        self.csv_file.close()

class ElasticsearchSavePipeline:
    def __init__(self, es_host):
        self.es = Elasticsearch(es_host)
        self.documents = []
        self.document_count = 0  # Biến đếm số tài liệu

    @classmethod
    def from_crawler(cls, crawler):
        es_host = crawler.settings.get('ELASTICSEARCH_HOST', 'http://localhost:9200')
        return cls(es_host)

    def process_item(self, item, spider):
        # Lưu vào danh sách documents
        doc = {
            'url': item['url'],
            'title': item['title'],
            'description': item['description'],
            'pubDate': item['pubDate'],
            'crawled_at': datetime.now().isoformat()
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
                spider.logger.error(f"Lỗi khi lưu vào Elasticsearch: {e}")

        return item

    def close_spider(self, spider):
        # Lưu tất cả tài liệu còn lại vào Elasticsearch khi spider đóng
        if self.documents:
            try:
                index_documents_with_embeddings(self.es, self.documents)
            except Exception as e:
                spider.logger.error(f"Lỗi khi lưu vào Elasticsearch: {e}")

class ChromaDBPipeline:
    def __init__(self, chromadb_host):
        # Khởi tạo Chroma với embedding function
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vector_store = Chroma(
            collection_name="example_collection",
            embedding_function=self.embeddings,
            persist_directory="./chroma_langchain_db"
        )

    @classmethod
    def from_crawler(cls, crawler):
        chromadb_host = crawler.settings.get('CHROMADB_HOST', 'http://localhost:8000')
        return cls(chromadb_host)

    def process_item(self, item, spider):
        # Tạo tài liệu để lưu vào ChromaDB
        doc = {
            'url': item['url'],
            'title': item['title'],
            'description': item['description'],
            'pubDate': item['pubDate'],
            'crawled_at': datetime.now().isoformat()
        }

        # Lưu tài liệu vào ChromaDB
        try:
            self.vector_store.add_documents(documents=[doc])
        except Exception as e:
            spider.logger.error(f"Lỗi khi lưu vào ChromaDB: {e}")

        return item

    def close_spider(self, spider):
        # Thực hiện các hành động cần thiết khi spider đóng
        pass
