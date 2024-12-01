import scrapy
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
import sqlite3
import html2text

class LinkSpider(scrapy.Spider):
    name = "link_spider"
    allowed_domains = ["docs.llamaindex.ai", "llamaindex.ai"]  # Replace with your target domain
    start_urls = ["https://docs.llamaindex.ai/en/stable/understanding/workflows/branches_and_loops/"]  # Replace with the starting URL

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = sqlite3.connect("../chatbot.db")
        self.cursor = self.connection.cursor()

    def parse(self, response):
        # Check if the URL already exists in the database
        self.cursor.execute("SELECT 1 FROM pages WHERE url = ?", (response.url,))
        if self.cursor.fetchone():
            self.logger.info(f"URL already exists in the database: {response.url}")
            return

        # Extract text content and convert to Markdown format
        soup = BeautifulSoup(response.text, 'html.parser')
        article_content = soup.select_one('article.md-content__inner.md-typeset')
        if article_content:
            soup = article_content
        text_content = html2text.html2text(str(soup))
       
        print('parse:url:', response.url)
        # Save the current page's text content
        yield {
            'url': response.url,
            'text_content': text_content  # Markdown formatted text content of the page
        }

        # Extract all links on the current page
        link_extractor = LinkExtractor()
        links = link_extractor.extract_links(response)
        
        # Follow each link and call the same parse method
        for link in links:
            yield response.follow(link.url, callback=self.parse)

    def closed(self, reason):
        self.connection.close()
