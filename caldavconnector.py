import caldav
from datetime import datetime
from datetime import timedelta
import pytz
import json

class CaldavConnector(object):
    
    def __init__(self,json_config):
        self.client = caldav.DAVClient(url=json_config["url"],username=json_config["user"],password=json_config["pass"])
        self.my_principal = self.client.principal()
        self.calendar = self.my_principal.calendar(json_config["calendar"])

    def update_calendar_data(self):
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
        # Interate through events and search for room categories            
        for event in events_fetched:
            for category in event.icalendar_component["categories"].cats:
                room_name = category.to_ical().decode()
                if room_name not in events_per_room.keys():
                    events_per_room[room_name] = []
                events_per_room[room_name].append(event)
        # Return events per room
        return events_per_room
