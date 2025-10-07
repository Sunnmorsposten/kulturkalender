from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy import signals

from src.newsscraper.newsscraper.spiders.parkenkulturhus import ParkenKulturhusSpider
from src.newsscraper.newsscraper.spiders.lovenvoldtheater import LovenvoldTheaterSpider
from src.newsscraper.newsscraper.spiders.fabrikkenkulturscene import FabrikkenKultursceneSpider
from src.newsscraper.newsscraper.spiders.pircowork import PirCoworkSpider
from src.newsscraper.newsscraper.spiders.terminalenbyscene import TerminalenBysceneSpider

configure_logging({"LOG_LEVEL": "INFO"})

def all_done():
    print("✓ All spiders finished")

if __name__ == "__main__":
    process = CrawlerProcess(settings={
        "CLOSESPIDER_TIMEOUT": 300,
        "TELNETCONSOLE_ENABLED": False,
        "LOG_LEVEL": "DEBUG",
        "DUPEFILTER_DEBUG": True,
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    for spider in [
        ParkenKulturhusSpider,
        LovenvoldTheaterSpider,
        FabrikkenKultursceneSpider,
        PirCoworkSpider,
        TerminalenBysceneSpider,
    ]:
        crawler = process.create_crawler(spider)
        crawler.signals.connect(all_done, signal=signals.spider_closed)
        process.crawl(crawler)
    process.start()