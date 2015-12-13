#!/usr/bin/env python

"""
A script for collecting data about various shows going on and aggregating them
into a single output file.
"""

import json
import os
import requests
import sys

from datetime import date, timedelta

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from mgrok.pipelines.json_pipeline import JsonWriterPipeline
from mgrok.scrapers import (
    BoweryBallroomSpider,
    MercuryLoungeSpider,
    MusicHallOfWilliamsburgSpider,
    RoughTradeSpider,
    TerminalFiveSpider,
    HighlineBallroomSpider,
    WarsawSpider
    )

TICKETFLY_DAYS_AHEAD = 3 * 31

TICKETFLY_API_BASE_URL = 'http://www.ticketfly.com/api'

TICKETFLY_API_VENUES = {
    'Brooklyn Bowl': '1',
    'Capitol Theatre': '4725'
    }

SCRAPY_SPIDERS = [
    WarsawSpider,
    HighlineBallroomSpider,
    BoweryBallroomSpider,
    MercuryLoungeSpider,
    MusicHallOfWilliamsburgSpider,
    RoughTradeSpider,
    TerminalFiveSpider,
    ]


def get_scraped_sites_data():
    """
    Returns output for venues which need to be scraped.
    """
    class RefDict(dict):
        """
        A dictionary which returns a reference to itself when deepcopied.
        """
        def __deepcopy__(self, memo):
            return self

    output = RefDict()

    settings = Settings({
        'LOG_ENABLED': False,
        'ITEM_PIPELINES': {
            'mgrok.pipelines.json_pipeline.JsonWriterPipeline': 1
            },
        'PIPELINE_OUTPUT': output
        })

    crawler_process = CrawlerProcess(settings)
    for spider in SCRAPY_SPIDERS:
        crawler_process.crawl(spider)

    crawler_process.start()

    return output


def get_api_sites_data():
    """
    Returns output for venues which provide api access.
    """
    list_event_endpoint = os.path.join(TICKETFLY_API_BASE_URL, "events/list")
    fromDate = date.today().strftime("%Y-%m-%d 00:00:00"),
    thruDate = (
        date.today() +
        timedelta(TICKETFLY_DAYS_AHEAD)).strftime("%Y-%m-%d 23:59:59")

    request_params = {
        'maxResults': 1000,
        'venueId': ','.join(TICKETFLY_API_VENUES.values()),
        'fromDate': fromDate,
        'thruDate': thruDate,
        }
    response = requests.get(list_event_endpoint, params=request_params)

    currentPage = response.json()['pageNum']
    totalPages = response.json()['totalPages']
    events = []
    while(True):
        events.extend(response.json()['events'])
        nextPage = currentPage + 1
        if nextPage > totalPages:
            break
        request_params.update({'pageNum': nextPage})
        response = requests.get(list_event_endpoint, params=request_params)
        currentPage = nextPage

    filtered_response = {}
    for event in events:
        artists = []
        for headliner in event['headliners']:
            artists.append(headliner['name'])
        for supporter in event['supports']:
            artists.append(supporter['name'])
        venue_name = event['venue']['name']
        event_date = event['startDate']
        url = event['ticketPurchaseUrl']

        if venue_name not in filtered_response:
            filtered_response[venue_name] = []

        filtered_response[venue_name].append({
            'artists': artists,
            'venue_name': venue_name,
            'date': event_date,
            'event_link': url
            })

    return filtered_response


def main():
    shows = {}
    shows.update(get_scraped_sites_data())
    shows.update(get_api_sites_data())

    print json.dumps(shows, indent=2)


if __name__ == '__main__':
    sys.exit(main())
