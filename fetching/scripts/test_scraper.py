#!/usr/bin/env python

import json
import os
import sys

from mgrok.scrapers import *
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

SCRAPY_SPIDERS = [
    WarsawSpider,
    # HighlineBallroomSpider,
    # BoweryBallroomSpider,
    # MercuryLoungeSpider,
    # MusicHallOfWilliamsburgSpider,
    # RoughTradeSpider,
    # TerminalFiveSpider,
#    RockwoodStageOneSpider,
#    RockwoodStageTwoSpider,
#    RockwoodStageThreeSpider
#  WebsterHallSpider
    ]

def get_scraped_sites_data():
    """Returns output for venues which need to be scraped."""
    class RefDict(dict):
        """A dictionary which returns a reference to itself when deepcopied."""
        def __deepcopy__(self, memo):
            return self

    # Hack: we pass a dictionary which can't be deep-copied into the settings
    # so as to _return_ the scraper output. As far as I can tell, this is the
    # only way to return the scraper output to the script itself.
    output = RefDict()

    settings = Settings({
        'LOG_ENABLED': True,
        'ITEM_PIPELINES': {
            'mgrok.pipelines.JsonWriterPipeline': 1
            },
        'PIPELINE_OUTPUT': output,
        'USER_AGENT': 'Chrome/41.0.2228.0'
        })

    crawler_process = CrawlerProcess(settings)
    for spider in SCRAPY_SPIDERS:
        crawler_process.crawl(spider)

    crawler_process.start()

    return output


def main():
  print json.dumps(get_scraped_sites_data(), indent=2)
  return os.EX_OK

if __name__ == '__main__':
    sys.exit(main())
