#!/usr/bin/env python

"""
A script for collecting data about various shows going on and aggregating them
into a single output file.
"""

import json
import os
import sys
from datetime import date, datetime, timedelta
from operator import attrgetter

from mgrok.scrapers import (
    BoweryBallroomSpider,
    MercuryLoungeSpider,
    MusicHallOfWilliamsburgSpider,
    RoughTradeSpider,
    TerminalFiveSpider,
    HighlineBallroomSpider,
    WarsawSpider
    )
from dateutil.parser import parse as parse_date_str
import pytz
import requests
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

TICKETFLY_DAYS_AHEAD = 3 * 31

TICKETFLY_API_BASE_URL = 'http://www.ticketfly.com/api'

TICKETFLY_API_VENUES = {
    'Brooklyn Bowl': '1',
    'Capitol Theatre': '4725'
    }

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
    """Returns output for venues which provide api access."""

    def make_request(page_num=1):
        """Returns the response from querying the ticketfly api."""
        list_event_endpoint = os.path.join(
            TICKETFLY_API_BASE_URL, "events/list")
        from_date = date.today().strftime("%Y-%m-%d 00:00:00"),
        thru_date = (
            date.today() +
            timedelta(TICKETFLY_DAYS_AHEAD)).strftime("%Y-%m-%d 23:59:59")
        request_params = {
            'maxResults': 1000,
            'venueId': ','.join(TICKETFLY_API_VENUES.values()),
            'fromDate': from_date,
            'thruDate': thru_date,
            'pageNum': page_num,
            }

        return requests.get(list_event_endpoint, params=request_params)

    def filter_events(events):
        """
        Filter API-returned event objects into more concise application-specific
        event objects
        """
        filtered_events = {}
        for event in events:
            artists = []
            for headliner in event['headliners']:
                artists.append(headliner['name'])
            for supporter in event['supports']:
                artists.append(supporter['name'])
            venue_name = event['venue']['name']

            time_zone = pytz.timezone(event['venue']['timeZone'])
            event_date = time_zone.localize(
                datetime.strptime(event['startDate'], '%Y-%m-%d %H:%M:%S'))
            url = event['ticketPurchaseUrl']

            if venue_name not in filtered_events:
                filtered_events[venue_name] = []

            filtered_events[venue_name].append({
                'artists': artists,
                'venue_name': venue_name,
                'date': event_date.isoformat(),
                'event_link': url
                })

        return filtered_events

    # Collect all event data
    response = make_request()
    events = []
    current_page = response.json()['pageNum']
    total_pages = response.json()['totalPages']
    while True:
        events.extend(response.json()['events'])
        next_page = current_page + 1
        if next_page > total_pages:
            break
        response = make_request(next_page)
        current_page = next_page

    return filter_events(events)


def main():
    """
    Collects event data from various sources, aggregates said data in a single
    object, and prints that object
    """
    # TODO add rockwood, drom
    shows = {}

    # Collect shows
    shows.update(get_scraped_sites_data())
    shows.update(get_api_sites_data())

    # Sort shows
    def key_function(event):
      date_str = event['date']
      return parse_date_str(date_str)
    for venue, events in shows.iteritems():
      events.sort(key=key_function)

    # Print shows
    print json.dumps(shows)

if __name__ == '__main__':
    sys.exit(main())
