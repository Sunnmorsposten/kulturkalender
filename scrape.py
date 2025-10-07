from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy import signals

from src.newsscraper.newsscraper.spiders.parkenkulturhus import ParkenKulturhusSpider

configure_logging({"LOG_LEVEL": "INFO"})

def all_done():
    print("✓ All spiders finished")

if __name__ == "__main__":
    process = CrawlerProcess(settings={
        "CLOSESPIDER_TIMEOUT": 300,
        "TELNETCONSOLE_ENABLED": False,
        "LOG_LEVEL": "INFO"
    })
    for spider in [
        ParkenKulturhusSpider,
    ]:
        crawler = process.create_crawler(spider)
        crawler.signals.connect(all_done, signal=signals.spider_closed)
        process.crawl(crawler)
    process.start(blocking=True)