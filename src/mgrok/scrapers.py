import scrapy

class _BoweryPresentsSpider(scrapy.Spider):
    def parse(self, response):
        selector = '.tfly-calendar .one-event .headliners > a::attr(href)'
        for event_link in response.css(selector):
            full_url = response.urljoin(event_link.extract())
            yield scrapy.Request(full_url, callback=self.parse_event)

    def parse_event(self, response):
        artists = (response
                   .css('.artist-boxes .artist-name')
                   .xpath('./text()').extract())
        date = response.css('.event-info .dates').xpath('./text()').extract()[0]
        yield {
            'event_link': response.url,
            'artists': artists,
            'date': date,
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

class _TicketWebSpider(scrapy.Spider):
    def parse(self, response):
        selector = '#LIST_VIEW .event-col .name a::attr(href)'
        for event_link in response.css(selector):
            full_url = response.urljoin(event_link.extract())
            yield scrapy.Request(full_url, callback=self.parse_event)

    def parse_event(self, response):
        artists = (response
                   .css('.artist-text .highlight span')
                   .xpath('./text()').extract())
        date = (
            response.css('.artist-text p')
            .xpath('./text()[count(preceding-sibling::br) < 1]').extract()[0])
        yield {
            'event_link': response.url,
            'artists': artists,
            'date': date.strip(),
            'venue_name': self.name
        }

class HighlineBallroomSpider(_TicketWebSpider):
    name = "Highline Ballroom"
    start_urls = [
        'http://www.ticketweb.com/snl/VenueListings.action?venueId=19776&pl='
        ]

class WarsawSpider(_TicketWebSpider):
    name = "Warsaw"
    start_urls = [
        'http://www.ticketweb.com/snl/VenueListings.action?venueId=22869&pl='
        ]
