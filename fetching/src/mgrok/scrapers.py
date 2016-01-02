"""
A set of scrapy spider subclasses for groking event information from various
venues.
"""

import re
from datetime import datetime, timedelta

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
            timezone = pytz.timezone('America/New_York')
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
        num_pages = len(response.css('.pagination-nav li'))
        for page_number in range(0, num_pages):
            yield scrapy.Request(
                response.urljoin('?page={0}'.format(page_number+1)),
                callback=self._parse_event_list)

    def _parse_event_list(self, response):
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
            .css('.artist-text .highlight span'))
        if not artists:
            yield None
        artists = artists.xpath('./text()').extract()
        date_text = (
            response
            .css('#edp-artist-Col .artist-text p')
            .xpath('./text()'))
        if not date_text:
            yield None
        date_text = date_text[0].extract().strip()
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
        timezone = pytz.timezone('America/New_York')
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


class _RockwoodSpider(scrapy.Spider):
    """Base class for Rockwood spiders"""
    start_urls = ['http://www.rockwoodmusichall.com/']
    selector = None

    def parse(self, response):
        for first_column in response.css(self.selector):
            date_str = first_column.css('h2').xpath('./text()').extract()[0]
            match = re.match(r'(\d\d)\.(\d\d).+', date_str)
            month = int(match.group(1))
            day_of_month = int(match.group(2))
            for artist_row in first_column.css('.sched_pod tr'):
                tds = artist_row.css('td')
                if not tds:
                    continue
                time_str = tds[0].xpath('./text()').extract()
                if not time_str:
                    continue
                match = re.match(r'(\d+):(\d\d)([ap]m)', time_str[0])
                if not match:
                    continue
                hour = int(match.group(1))
                minute = int(match.group(2))
                ampm = match.group(3)

                if ampm == 'am':
                    hour %= 12
                else:
                    hour += 12

                event_date = datetime(
                    datetime.now().year, month, day_of_month,
                    hour, minute, 0, 0)
                event_date = (
                    pytz.timezone('America/New_York').localize(event_date))
                if ampm == 'am':
                    event_date += timedelta(1)

                artist = (
                    artist_row
                    .css('td')[1]
                    .css('a')
                    .xpath('./text()')
                    .extract())
                if not artist:
                    continue

                yield {
                    'event_link': self.start_urls[0],
                    'artists': artist,
                    'date': event_date.isoformat(),
                    'venue_name': self.name
                    }


class RockwoodStageOneSpider(_RockwoodSpider):
    selector = '.first_column'
    name = "Rockwood (Stage 1)"

class RockwoodStageTwoSpider(_RockwoodSpider):
    selector = '.second_column'
    name = "Rockwood (Stage 2)"

class RockwoodStageThreeSpider(_RockwoodSpider):
    selector = '.third_column'
    name = "Rockwood (Stage 3)"

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

class WebsterHallSpider(_TicketWebSpider):
    name = "Webster Hall"
    start_urls = [
        'http://www.ticketweb.com/venue/webster-hall-new-york-ny/10015'
        ]
