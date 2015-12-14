"""
Pipelines for extracting data from venue-scraping scrapy spiders
"""

class JsonWriterPipeline(object):
    """
    JSON extracting scraper pipeline
    """
    def __init__(self, items):
        self.items_ = items

    @classmethod
    def from_settings(cls, settings):
        return cls(settings['PIPELINE_OUTPUT'])

    def process_item(self, item, scraper):
        """
        Adds items to the output dictionary.
        """
        if item['venue_name'] not in self.items_:
            self.items_[item['venue_name']] = []
        self.items_[item['venue_name']].append(dict(item))
        return item
