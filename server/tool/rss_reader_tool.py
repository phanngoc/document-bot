# RSS Read

# from langchain_community.document_loaders import RSSFeedLoader

# urls = ["https://vnexpress.net/rss/thoi-su.rss"]

# loader = RSSFeedLoader(urls=urls)
# data = loader.load()
# print(len(data))

# print(data[0].page_content)


from langchain_core.tools import tool
from scrapy.crawler import CrawlerProcess
import datetime
# Get the current date and time
now = datetime.datetime.now()


from spiders.rss_spider import RssSpider
from langchain_community.document_loaders import CSVLoader

@tool(response_format="content_and_artifact")
def retrieve_rss_link(url: str):
    """Retrieve rss link from user query."""
    formatted_time = now.strftime("%Y%m%d_%H%M") + ".csv"
    runner = CrawlerProcess()
    runner.crawl(RssSpider, start_url=url, output_file=formatted_time, max_urls=500)
    runner.start()

    full_path_csv = "data_temp/rss_data/" + formatted_time
    loader = CSVLoader(file_path=full_path_csv,
        csv_args={
        'delimiter': ',',
        'quotechar': '"',
    })

    docs = loader.load()
    print(docs[0].page_content[:100])
    print(docs[0].metadata)

    return docs