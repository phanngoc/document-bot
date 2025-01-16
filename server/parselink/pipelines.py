# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3
import json

class SQLitePipeline:
    def open_spider(self, spider):
        self.connection = sqlite3.connect('../chatbot.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            text_content JSON,
            assistant_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assistant_id) REFERENCES assistants(id)
            )
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url ON pages (url)
        ''')
        self.connection.commit()

    def close_spider(self, spider):
        self.connection.close()

    def process_item(self, item, spider):
        text_content_json = json.dumps(item['text_content'])
        self.cursor.execute('''
            INSERT OR REPLACE INTO pages (url, text_content, assistant_id, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (item['url'], text_content_json, item['assistant_id']))
        self.connection.commit()
        return item
