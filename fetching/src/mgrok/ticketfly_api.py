"""
Classes for collecting venue information from the venues who use TicketFly
"""

from datetime import date, datetime, timedelta
import os
import re

import requests
import pytz

class _TicketFlyApi(object):
    """
    Base class for fetching data from ticketfly api.
    """
    base_url = 'http://www.ticketfly.com/api'
    days_behind = 7
    days_ahead = 3 * 31

    def __init__(self, venue_id, org_id=None):
        self.venue_id = venue_id
        self.org_id = org_id

    def make_request(self, page_num=1):
        """Returns the response from querying the ticketfly api."""
        list_event_endpoint = os.path.join(self.base_url, "events/list")
        from_date = (
            date.today() -
            timedelta(self.days_behind)).strftime("%Y-%m-%d 00:00:00")
        thru_date = (
            date.today() +
            timedelta(self.days_ahead)).strftime("%Y-%m-%d 23:59:59")
        request_params = {
            'maxResults': 1000,
            'venueId': self.venue_id,
            'fromDate': from_date,
            'thruDate': thru_date,
            'pageNum': page_num,
            }
        if self.org_id:
            request_params['orgId'] = self.org_id

        return requests.get(list_event_endpoint, params=request_params)

    def format_events(self, events):
        """
        Filter API-returned event objects into more concise application-specific
        event objects
        """
        formatted_events = {}
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

            if venue_name not in formatted_events:
                formatted_events[venue_name] = []

            formatted_events[venue_name].append({
                'artists': artists,
                'venue_name': venue_name,
                'date': event_date.isoformat(),
                'event_link': url
                })


        for venue_name, event_list in formatted_events.iteritems():
            formatted_events[venue_name] = (
                self.venue_specific_filter(event_list))
        return formatted_events

    def venue_specific_filter(self, events):
        return events

    def get_api_sites_data(self):
        response = self.make_request()
        events = []
        current_page = response.json()['pageNum']
        total_pages = response.json()['totalPages']
        while True:
            events.extend(response.json()['events'])
            next_page = current_page + 1
            if next_page > total_pages:
                break
            response = self.make_request(next_page)
            current_page = next_page

        return self.format_events(events)


class BrooklynBowlApi(_TicketFlyApi):
    """Fetches data for events at Brooklyn Bowl"""
    def __init__(self):
        super(BrooklynBowlApi, self).__init__(1, 3)

    def venue_specific_filter(self, events):
        def filter_family_bowl(event):
            for artist in event['artists']:
                regex = re.compile(r'.*family bowl.*', re.IGNORECASE)
                if re.match(regex, artist):
                    return False
            return True

        return filter(filter_family_bowl, events)


class CapitolTheatreApi(_TicketFlyApi):
    """Fetches data for events at The Capitol Theatre"""
    def __init__(self):
        super(CapitolTheatreApi, self).__init__(4725, 767)


class GarciasAtTheCapitolTheatreApi(_TicketFlyApi):
    """Fetches data for events at Garcia's At The Capitol Theatre"""
    def __init__(self):
        super(GarciasAtTheCapitolTheatreApi, self).__init__(8211, 2703)


class StVitusApi(_TicketFlyApi):
    """Fetches data for events at St Vitus"""
    def __init__(self):
        super(StVitusApi, self).__init__(1851, 663)
