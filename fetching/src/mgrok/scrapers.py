"""
A set of scrapy spider subclasses for groking event information from various
venues.
"""

import re
from datetime import datetime

import pytz
import scrapy

class _BoweryPresentsSpider(scrapy.Spider):
    """
    Base class spider for Bowery Presents formatted venue websites
    """
    def parse(self, response):
        selector = '.tfly-calendar .one-event .headliners > a::attr(href)'
        for event_link in response.css(selector):
            full_url = response.urljoin(event_link.extract())
            yield scrapy.Request(full_url, callback=self._parse_event)

    def _parse_event(self, response):
        artists = (response
                   .css('.artist-boxes .artist-name')
                   .xpath('./text()').extract())
        date = (
            response
            .css('.event-info .times .value-title::attr(title)')
            .extract())
        if not date:
            date = (
                response
                .css('.event-info .dates').xpath('./text()')
                .extract()[0]
                .strip())
            time = (
                response
                .css('.event-info .times .doors').xpath('./text()')
                .extract()[0].lstrip('Doors: '))
            timezone = pytz.timezone('US/Eastern')
            the_datetime = timezone.localize(
                datetime.strptime(
                    date + ' ' + time,
                    '%a, %B %d, %Y %I:%M %p'))
            date = the_datetime.isoformat()
        else:
            date = date[0]

        yield {
            'event_link': response.url,
            'artists': artists,
            'date': date,
            'venue_name': self.name
        }

class _TicketWebSpider(scrapy.Spider):
    """Base class spider for ticketweb formatted venue websites"""

    EVENT_URL_FORMAT = (
        'http://www.ticketweb.com/t3/sale/SaleEventDetail'
        '?dispatch=loadSelectionData&eventId=')

    def parse(self, response):
        selector = '.event-list .media-body .event-name a::attr(href)'
        for event_link in response.css(selector):
            # The link has angular template garbage in it, so we generate our
            # own link to the event
            match = re.search(r'eventId=(\d+)', event_link.extract())
            full_url = response.urljoin(self.EVENT_URL_FORMAT + match.group(1))
            yield scrapy.Request(full_url, callback=self._parse_event)

    def _parse_event(self, response):
        artists = (
            response
            .css('.artist-text .highlight span')
            .xpath('./text()')
            .extract())
        date_text = (
            response
            .css('#edp-artist-Col .artist-text p')
            .xpath('./text()')
            .extract()[0]
            .strip())
        match = re.match(
            r'^'
            r'(?P<day_of_week>\w+), '
            r'(?P<abreviated_month>\w+) '
            r'(?P<day_of_month>\d+), '
            r'(?P<year>\d{4}) '
            r'(?P<hour>\d+):'
            r'(?P<minute>\d+) '
            r'(?P<am_pm>[AP]M) '
            r'(?P<timezone>\w+)', date_text)
        no_tz_date_str = date_text[0:match.end('am_pm')].strip()
        timezone = pytz.timezone('US/Eastern')
        the_datetime = timezone.localize(
            datetime.strptime(
                no_tz_date_str,
                '%A, %b %d, %Y %I:%M %p'),
            match.group('timezone') == 'EDT')

        yield {
            'event_link': response.url,
            'artists': artists,
            'date': the_datetime.isoformat(),
            'venue_name': self.name
        }

class BoweryBallroomSpider(_BoweryPresentsSpider):
    name = 'Bowery Ballroom'
    start_urls = ['http://www.boweryballroom.com/calendar/']

class MercuryLoungeSpider(_BoweryPresentsSpider):
    name = 'Mercury Lounge'
    start_urls = ['http://www.mercuryloungenyc.com/calendar']

class MusicHallOfWilliamsburgSpider(_BoweryPresentsSpider):
    name = 'Music Hall of Williamsburg'
    start_urls = ['http://www.musichallofwilliamsburg.com/calendar']

class TerminalFiveSpider(_BoweryPresentsSpider):
    name = 'Terminal 5'
    start_urls = ['http://www.terminal5nyc.com/calendar']

class RoughTradeSpider(_BoweryPresentsSpider):
    name = 'Rough Trade'
    start_urls = ['http://www.roughtradenyc.com/calendar']

class HighlineBallroomSpider(_TicketWebSpider):
    name = "Highline Ballroom"
    start_urls = [
        'http://www.ticketweb.com/venue/highline-ballroom-new-york-ny/19776'
        ]

class WarsawSpider(_TicketWebSpider):
    name = "Warsaw"
    start_urls = [
        'http://www.ticketweb.com/venue/warsaw-brooklyn-ny/22869'
        ]
