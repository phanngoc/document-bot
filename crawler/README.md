scrapy startproject tutorial

# Create a new spider
cd crawler
scrapy genspider quotes quotes.toscrape.com

# Run the spider
- `scrapy crawl link_spider`
- `scrapy crawl link_spider -a start_url="https://python.langchain.com/docs/integrations/document_loaders/" -a assistant_id=1`
