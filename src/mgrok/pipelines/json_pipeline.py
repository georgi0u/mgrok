import json
import sys

class JsonWriterPipeline(object):
    def __init__(self, items):
        self.items_ = items

    @classmethod
    def from_settings(cls, settings):
      return cls(settings['PIPELINE_OUTPUT'])

    def process_item(self, item, spider):
        if item['venue_name'] not in self.items_:
          self.items_[item['venue_name']] = []
        self.items_[item['venue_name']].append(dict(item))
        return item
