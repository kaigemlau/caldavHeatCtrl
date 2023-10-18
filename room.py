import caldav
from datetime import timedelta
from datetime import datetime
import pytz
from threading import Lock

# Room class with room properties and mqtt topics
class Room(object):
        
    """Init Room Class

    Parameters:
    name (str): Room-Name
    preheat_hours (int): How long before an event shall the heating be switched on
    target_temp_day, target_temp_night (float): Setpoints for control
    
    """
    def __init__(self,name,preheat_hours,target_temp_day=20.0,target_temp_night=15.0):
        # room name
        self.name = name
        # required time for pre-heating room
        self.preheat_hours = preheat_hours
        # current and target temperatures for control
        self.current_temp = 10.0
        self.target_temp_day = target_temp_day
        self.target_temp_night = target_temp_night
        # last time temperature was updated
        self.last_temp_update = datetime.now(pytz.utc)
        # heating valve on
        self.heating_on = False
        # switch status
        self.switch_status = False
        # Upcoming events
        self.events = []
        # event is pending, need to heat up?
        self.event_pending = False
        # last heating request time
        self.last_req_time = datetime.min.replace(tzinfo=pytz.UTC)
        # List of pending events
        self.events = []
        # Mutex for thread-safety
        self.lock = Lock()
    
    
    ''' Print Room instance (for debug purposes only) '''
    def __str__ (self):
        return "Room "+self.name+"\n"+\
                "--preheat_hours: "+str(self.preheat_hours)+"\n"+\
                "--number of events: "+str(len(self.events))+"\n"+\
                "--event is pending: "+str(self.event_pending)+"\n"+\
                "--temperatures [night; current; day]: ["+str(self.target_temp_night)+"; "+str(self.current_temp)+"; "+str(self.target_temp_day)+"]\n"+\
                "--last temp update: "+str(self.last_temp_update)+"\n"+\
                "--last req time: "+str(self.last_req_time)+"\n"+\
                "--heating on: "+str(self.heating_on)+"\n"
    
    ''' Check if there is either an upcoming (or ongoing) CalDAV event, or if there is a manual heating request pending '''
    def check_event_pending(self):
        self.event_pending = False
        dtnow = datetime.now(pytz.utc)
        #get room specific preheat time
        dtpreheat = timedelta(hours=self.preheat_hours)
        #iterate through all caldav events
        if len(self.events):
            for event in self.events:
                #for each event, check if we are in the interval [start-preheat, end]
                dtstart = event.icalendar_component.get("dtstart")
                dtend = event.icalendar_component.get("dtend")
                dtstart_dt = dtstart and dtstart.dt
                dtend_dt = dtend and dtend.dt
                if dtstart_dt - dtpreheat <= dtnow <= dtend_dt:
                    self.event_pending = True
        # check if we have a manual heating request
        if self.last_req_time <= dtnow <= self.last_req_time + dtpreheat:
            self.event_pending = True
    
    ''' Update current temperature '''    
    def update_temp(self, temp):
        self.lock.acquire()
        self.current_temp = temp
        self.last_temp_update = datetime.now(pytz.utc)
        self.lock.release()
     
    ''' update list of CalDAV events '''    
    def update_event_list(self,events):
        self.lock.acquire()
        self.events = events
        self.lock.release()
    
    ''' Update feedback from Shelly output status '''    
    def update_switch_status(self, status):
        self.lock.acquire()
        self.switch_status = status
        self.lock.release()
    
    ''' Trigger heating manually '''
    def manual_heating_request(self):
        self.lock.acquire()
        self.last_req_time = datetime.now(pytz.utc)
        self.heating_on = True
        self.lock.release()
    
    ''' Control loop for heating, decide which set-point temperature to use and control with hysteresis '''
    def control_heating(self):
        self.lock.acquire()
        self.check_event_pending()
        
        #select target temp based on event pending
        target_temp = self.target_temp_night
        if self.event_pending: 
            target_temp = self.target_temp_day
        
        #control temperature with hysteresis
        if self.current_temp <= target_temp - 0.5:
            self.heating_on = True
        if self.current_temp >= target_temp + 0.5:
            self.heating_on = False

        self.lock.release()
    
