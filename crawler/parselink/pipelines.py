# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3

class TutorialPipeline:
    def process_item(self, item, spider):
        return item

class SQLitePipeline:
    def open_spider(self, spider):
        self.connection = sqlite3.connect("../chatbot.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            text_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url ON pages (url)
        ''')
        self.connection.commit()

        self.cursor.execute('DELETE FROM pages')
        self.connection.commit()

    def close_spider(self, spider):
        self.connection.close()

    def process_item(self, item, spider):
        self.cursor.execute('''
            INSERT OR REPLACE INTO pages (id, url, text_content, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (item.get('id'), item['url'], item['text_content']))
        self.connection.commit()
        return item
