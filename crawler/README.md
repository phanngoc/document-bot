scrapy startproject tutorial

# Create a new spider
cd tutorial
scrapy genspider quotes quotes.toscrape.com

# Run the spider
scrapy crawl quotes
