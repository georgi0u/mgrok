"""
A set of scrapy spider subclasses for groking event information from various
venues.
"""

from datetime import datetime, timedelta
from functools import partial
import re

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
        the_date = (
            response
            .css('.event-info .times .value-title::attr(title)')
            .extract())
        if not the_date:
            the_date = (
                response
                .css('.event-info .dates').xpath('./text()')
                .extract()[0]
                .strip())
            the_time = (
                response
                .css('.event-info .times .doors').xpath('./text()')
                .extract()[0].lstrip('Doors: '))
            timezone = pytz.timezone('America/New_York')
            the_datetime = timezone.localize(
                datetime.strptime(
                    the_date + ' ' + the_time,
                    '%a, %B %d, %Y %I:%M %p'))
            the_date = the_datetime.isoformat()
        else:
            the_date = the_date[0]

        yield {
            'event_link': response.url,
            'artists': artists,
            'date': the_date,
            'venue_name': self.name
        }

class _TicketWebSpider(scrapy.Spider):
    """Base class spider for ticketweb formatted venue websites"""
    base_url_format = 'http://www.ticketweb.com/venue/{}'

    event_url_format = (
        'http://www.ticketweb.com/t3/sale/SaleEventDetail'
        '?dispatch=loadSelectionData&eventId=')

    def parse(self, response):
        pages = [
            scrapy.Request(response.url, callback=self._parse_event_list)
        ]
        num_pages = len(response.css('.pagination-nav li'))
        for page_number in range(1, num_pages):
            pages.append(
                scrapy.Request(
                    response.urljoin('?page={0}'.format(page_number+1)),
                    callback=self._parse_event_list))
        for page in pages:
            yield page

    def _parse_event_list(self, response):
        selector = '.event-list .media-body .event-name a::attr(href)'
        for event_link in response.css(selector):
            # The link has angular template garbage in it, so we generate our
            # own link to the event
            match = re.search(r'eventId=(\d+)', event_link.extract())
            full_url = response.urljoin(self.event_url_format + match.group(1))
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
            date_str = first_column.css('h2').xpath('./text()').extract()
            if not date_str:
                continue
            match = re.match(r'(\d\d)\.(\d\d).+', date_str[0])
            month = int(match.group(1))
            day_of_month = int(match.group(2))
            artists = []
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
                    artist = (
                        artist_row
                        .css('td')[1]
                        .css('strong')
                        .xpath('./text()')
                        .extract())
                if not artist:
                    continue
                artists.append({'artist': artist[0], 'date': event_date})

            artists.sort(key=lambda x: x['date'])
            artist_strings = []
            for artist in artists:
                the_date = (
                    artist['date']
                    .strftime('%I:%M')
                    .lstrip('0'))

                artist_strings.append(
                    u'{} ({})'.format(artist['artist'], the_date))
            if not artists:
                yield None
            else:
                yield {
                    'event_link': self.start_urls[0],
                    'artists': artist_strings,
                    'date': artists[0]['date'].isoformat(),
                    'venue_name': self.name
                }


class TheSpaceAtWestburySpider(scrapy.Spider):
    """
    This bastard uses tables for layout, and there are no id or class tags. Boo.
    TODO: Pick this up eventually.
    """
    name = 'The Space at Westbury'
    base_url = 'http://thespaceatwestbury.com/'
    start_urls = [base_url + '?page=shows']

    def parse(self, response):
        onclick_string_predicate = 'location.href=\'?page=show&sid='
        attribute_selector = (
            '//*[starts-with(@onclick, "{0}")]/'
            '@onclick'.format(onclick_string_predicate))
        for location in response.xpath(attribute_selector):
            event_url_suffix = location.extract().partition('?')[2]
            event_url = '{0}?{1}'.format(self.base_url, event_url_suffix)
            yield scrapy.Request(event_url, callback=self._parse_event)

    def _parse_event(self, response):
        yield None



class _MSGSpider(scrapy.Spider):
    base_url_format = (
        'http://www.beacontheatre.com/calendar'
        '?page=0&evmonth=&evtype=concert&venue={0}')

    def parse(self, response):
        event_links = response.css('td.event_name a').xpath('@href').extract()
        for event_url in event_links:
            if event_url[0] == '/':
                event_url = response.urljoin(event_url)
            yield scrapy.Request(event_url, callback=self._parse_event)

    def _parse_event(self, response):
        title = (
            response
            .css('#event-information .event-title')
            .xpath('./text()')
            .extract()[0])
        if not title:
            title = response.url

        events = []
        for event_date in response.css('.box-event-calendar'):
            short_month_str = (
                event_date
                .css('.m-event')
                .xpath('./text()')
                .extract()[0])

            day_str = (
                event_date
                .css('.number-day-event')
                .xpath('./text()')
                .extract()[0])

            year_str = (
                event_date
                .css('.d-event')
                .xpath('./text()')
                .extract()[0])

            time_str = (
                event_date
                .css('.time-event')
                .xpath('./text()')
                .extract()[0])

            datetime_str = '{} {} {} {}'.format(
                short_month_str,
                day_str,
                year_str,
                time_str)

            the_datetime = datetime.strptime(
                datetime_str,
                '%b %d %Y %I:%M %p')

            timezone = pytz.timezone('America/New_York')
            the_datetime = timezone.localize(the_datetime)

            events.append({
                'event_link': response.url,
                'artists': [title],
                'date': the_datetime.isoformat(),
                'venue_name': self.name
            })
        yield {'events': events}

class CityWinerySpider(scrapy.Spider):
    """
    Base class spider for City Winery
    """
    start_urls = [
        'http://www.citywinery.com/newyork/tickets.html' +
        '?cat=40&limit=100&p=0&view=list'
    ]
    name = 'City Winery'
    def parse(self, response):
        event_wrapper = response.css('.tickets-content.products-container dl')
        for event in event_wrapper:
            event_link = (
                event
                .css('p.addtocart a')
                .xpath('./@href')
                .extract()[0])
            date_str = (
                event
                .css('dt')
                .xpath('./text()')
                .extract()[0]
                .strip()
            )

            yield scrapy.Request(
                event_link,
                callback=partial(self._parse_event, date_str)
            )

        next_page_link = response.css('a.next').xpath('./@href').extract()
        if next_page_link:
            yield scrapy.Request(next_page_link[0], callback=self.parse)
        else:
            yield None

    def _parse_event(self, date_str, response):
        times = (
            response
            .css('.event-head .left strong')
            .xpath('./text()')
            .extract()
        )
        the_time = times[0]
        for time in times:
            if re.search('start', time, re.IGNORECASE):
                the_time = time
        the_time = re.match(r'\d+:\d+ [AaPp][Mm]', the_time).group(0)
        the_datetime = datetime.strptime(
            date_str + ' ' + the_time,
            '%A, %B %d %I:%M %p')
        now = datetime.now()
        year = now.year
        if the_datetime.month < now.month:
            year += 1
        the_datetime = the_datetime.replace(year=year)
        timezone = pytz.timezone('America/New_York')
        the_datetime = timezone.localize(the_datetime)

        title = response.css('.event-head h1').xpath('./text()').extract()[0]
        title_match = re.match(r'(.+)-', title)
        if title_match:
            title = title_match.group(1).strip()
        yield {
            'event_link': response.url,
            'artists': [title],
            'date': the_datetime.isoformat(),
            'venue_name': self.name
        }

class MSGSpider(_MSGSpider):
    name = 'Madison Square Garden'
    start_urls = [_MSGSpider.base_url_format.format('gardens')]

class TheBeaconSpider(_MSGSpider):
    name = 'The Beacon Theatre'
    start_urls = [_MSGSpider.base_url_format.format('beacon')]

class TheTheaterAtMSGSpider(_MSGSpider):
    name = 'The Theater at Madison Square Garden'
    start_urls = [_MSGSpider.base_url_format.format('theatermsg')]

class RadioCitySpider(_MSGSpider):
    name = 'Radio City Music Hall'
    start_urls = [_MSGSpider.base_url_format.format('radiocity')]

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
        _TicketWebSpider.base_url_format.format(
            'highline-ballroom-new-york-ny/19776')
    ]

class WarsawSpider(_TicketWebSpider):
    name = "Warsaw"
    start_urls = [
        _TicketWebSpider.base_url_format.format('warsaw-brooklyn-ny/22869')
    ]

class WebsterHallSpider(_TicketWebSpider):
    name = "Webster Hall"
    start_urls = [
        _TicketWebSpider.base_url_format.format(
            'webster-hall-new-york-ny/10015')
    ]

class TheStudioAtWebsterHallSpider(_TicketWebSpider):
    name = "The Studio at Webster Hall"
    start_urls = [
        _TicketWebSpider.base_url_format.format(
            'the-studio-at-webster-hall-new-york-ny/71954')
    ]

class KnittingFictorySpider(_TicketWebSpider):
    name = "Knitting Factory"
    start_urls = [
        _TicketWebSpider.base_url_format.format(
            'knitting-factory-brooklyn-brooklyn-ny/221784')
    ]

class TheBoweryElectricSpider(_TicketWebSpider):
    name = "The Bowery Electric"
    start_urls = [
        _TicketWebSpider.base_url_format.format(
            'map-room-at-bowery-electric-new-york-ny/31434'),
        _TicketWebSpider.base_url_format.format(
            'the-bowery-electric-new-york-ny/97554')
    ]
