#!/usr/bin/env python

"""
A script for collecting data about various shows going on and aggregating them
into a single output file.
"""

from datetime import datetime
import argparse
import json
import sys

from mgrok.scrapers import (
    BoweryBallroomSpider,
    MercuryLoungeSpider,
    MusicHallOfWilliamsburgSpider,
    RoughTradeSpider,
    TerminalFiveSpider,
    HighlineBallroomSpider,
    WarsawSpider
    )
from mgrok.ticketfly_api import (
    BrooklynBowlApi,
    CapitolTheatreApi
    )
from dateutil.parser import parse as parse_date_str
from pytz import timezone
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings


SCRAPY_SPIDERS = [
    WarsawSpider,
    HighlineBallroomSpider,
    # Bowery
    BoweryBallroomSpider,
    MercuryLoungeSpider,
    MusicHallOfWilliamsburgSpider,
    RoughTradeSpider,
    TerminalFiveSpider,
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
        'LOG_ENABLED': False,
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


def get_api_sites_data():
    """Returns output for venues which have APIs"""
    output = {}
    output.update(BrooklynBowlApi().get_api_sites_data())
    output.update(CapitolTheatreApi().get_api_sites_data())
    return output

def main():
    """
    Collects event data from various sources, aggregates said data in a single
    object, and prints that object
    """
    parser = argparse.ArgumentParser(description='see whats playing in nyc.')
    parser.add_argument('outfile', type=argparse.FileType('w'))

    args = parser.parse_args()

    # TODO add rockwood, drom
    shows = {}

    # Collect shows
    shows.update(get_scraped_sites_data())
    shows.update(get_api_sites_data())

    # Sort shows
    def key_function(event):
        date_str = event['date']
        return parse_date_str(date_str)
    for events in shows.values():
        events.sort(key=key_function)

    output = {
        "updated": datetime.now(timezone('US/Eastern')).isoformat(),
        "shows": shows
        }

    # Print shows
    args.outfile.write(json.dumps(output))

if __name__ == '__main__':
    sys.exit(main())
