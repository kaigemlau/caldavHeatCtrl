import sys
import json
from room import Room
from mqttconnector import MQTTConnector
from caldavconnector import CaldavConnector
import time

rooms = {}

def init_rooms(json_config):
    for cfg in json_config:
        rooms[cfg["name"]] = Room(cfg["name"],cfg["preheat_hours"],cfg["target_temp_day"],cfg["target_temp_night"])

def temp_update_callback(r_name,temp):
    print("Temp update "+r_name+" "+str(temp))
    if r_name in rooms.keys():
        rooms[r_name].update_temp(temp)
    
def switch_update_callback(r_name,status):
    if r_name in rooms.keys():
        rooms[r_name].update_switch_status(status)
        
def heating_request_callback(r_name):
    if r_name in rooms.keys():
        rooms[r_name].manual_heating_request()        

if __name__ == "__main__":
    #Read config from json
    with open("config/config.json") as json_data_file:
        cfg_data = json.load(json_data_file)
    # create rooms
    init_rooms(cfg_data["rooms"])
    # connect to caldav server
    calCon = CaldavConnector(cfg_data["caldav"])
    # connect to mqtt broker
    mqttCon = MQTTConnector(cfg_data["mqtt"])
    mqttCon.temp_update_callback = temp_update_callback
    mqttCon.switch_update_callback = switch_update_callback
    mqttCon.heating_request_callback = heating_request_callback
    
    print("Init done, starting loop")
    
    s_count = 0
    while True:
        if s_count % 60 == 0:
            # Update sensor status every 60s
            for r_name in rooms.keys():
                mqttCon.request_status_update(r_name)
        if s_count % 600 == 0:
            # Update calendar data every 10min
            events_per_room = calCon.update_calendar_data()
            if events_per_room:
                for r_name in events_per_room.keys():
                    if r_name in rooms.keys():
                        rooms[r_name].update_event_list(events_per_room[r_name])
        if s_count % 10 == 0:
            # Process room controller every 10s
            for room in rooms.values():
                room.control_heating()
                
        for room in rooms.values():
            if room.heating_on != room.switch_status:
                print("Need to switch "+room.name+" "+str(room.heating_on))
                print(room)
                mqttCon.request_switch_ctrl(room.name,room.heating_on)
                mqttCon.request_status_update(r_name)
        time.sleep(1)
        s_count += 1
    
    
