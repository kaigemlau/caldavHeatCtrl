import caldav
from datetime import datetime
from datetime import timedelta
import pytz
import json

class CaldavConnector(object):
    
    """Init CalDAV Connector

    Parameters:
    json_config: JSON data used for configuration. see config/config.json.sample for details
    
    """
    def __init__(self,json_config):
        self.client = caldav.DAVClient(url=json_config["url"],username=json_config["user"],password=json_config["pass"])
        self.my_principal = self.client.principal()
        self.calendar = self.my_principal.calendar(json_config["calendar"])

    ''' Fetch current calendar data (-1 day, +7days) and sort by category for rooms. Will ignore sporadic connection errors '''
    def update_calendar_data(self):
        try:
            # Get current time
            dtnow = datetime.now(pytz.utc)
            # Fetch current and upcoming events    
            events_fetched = self.calendar.search(
                start=(dtnow - timedelta(days=1)),
                end=(dtnow + timedelta(days=7)),
                event=True,
                expand=True,
            )
            # Reset list of events per room
            events_per_room = {}
            # Iterate through events and search for room categories            
            for event in events_fetched:
                for category in event.icalendar_component["categories"].cats:
                    room_name = category.to_ical().decode()
                    if room_name not in events_per_room.keys():
                        events_per_room[room_name] = []
                    events_per_room[room_name].append(event)
            # Return events per room
            return events_per_room
        except:
            print("CalDAV Error occurred! No data is read!")
            return None
