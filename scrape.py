from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy import signals

from src.newsscraper.newsscraper.spiders.brreg_announcement import BrregSpider
from src.newsscraper.newsscraper.spiders.bypakkealesund import BypakkealesundSpider
from src.newsscraper.newsscraper.spiders.fiskarlaget import FiskarlagetSpider
from src.newsscraper.newsscraper.spiders.fiskebat import FiskebatSpider
from src.newsscraper.newsscraper.spiders.hi import HiSpider
from src.newsscraper.newsscraper.spiders.kystverket import KystverketSpider
from src.newsscraper.newsscraper.spiders.nffoverganger import NffovergangerSpider
from src.newsscraper.newsscraper.spiders.pelagiskforening import PelagiskForeningSpider
from src.newsscraper.newsscraper.spiders.rafisklaget import RafisklagetSpider
from src.newsscraper.newsscraper.spiders.sjomatnorge import SjomatnorgeSpider
from src.newsscraper.newsscraper.spiders.surofi import SurofiSpider

configure_logging({"LOG_LEVEL": "INFO"})

def all_done():
    print("✓ All spiders finished")

if __name__ == "__main__":
    process = CrawlerProcess(settings={
        "CLOSESPIDER_TIMEOUT": 300,
        "TELNETCONSOLE_ENABLED": False
    })
    for spider in [
        BrregSpider,
        BypakkealesundSpider,
        FiskarlagetSpider,
        FiskebatSpider,
        HiSpider,
        KystverketSpider,
        NffovergangerSpider,
        PelagiskForeningSpider,
        RafisklagetSpider,
        SjomatnorgeSpider,
        SurofiSpider,
    ]:
        crawler = process.create_crawler(spider)
        crawler.signals.connect(all_done, signal=signals.spider_closed)
        process.crawl(crawler)
    process.start()