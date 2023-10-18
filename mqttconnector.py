import paho.mqtt.client as mqtt
import threading
import time
import json 
from room import Room

class MQTTConnector(object):
    
    temp_update_callback = None
    switch_update_callback = None
    heating_request_callback = None
    
    def __init__(self,json_config):
        #init mqtt client
        self.topic_base = json_config["topic_base"]
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(json_config["user"], json_config["pass"])
        self.client.connect(json_config["broker"], json_config["port"], 60)
        # prepare the worker thread
        self.mqtt_thread = threading.Thread(target=self.mqtt_thread_func)
        self.mqtt_thread.start()

    def mqtt_thread_func(self):
        self.client.loop_start()
        
    def on_connect(self,client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        client.subscribe(self.topic_base+"/#")
    
    def on_message(self,client,userdata,msg):
        topic = msg.topic.replace(self.topic_base+"/","")
        if len(topic.split('/')) == 3:
            room_name = topic.split('/')[0]
            if "status/temperature" in topic:
                # Store Temperature Update
                data = json.loads(msg.payload.decode("utf-8"))
                if self.temp_update_callback:
                    self.temp_update_callback(room_name,float(data["tC"]))
            elif "status/switch" in topic:
                # Store Switch Status Update
                data = json.loads(msg.payload.decode("utf-8"))
                if self.switch_update_callback:
                    self.switch_update_callback(room_name,bool(data["output"]))
            elif "events/rpc" in topic:
                # Event (button pressed)
                data = json.loads(msg.payload.decode("utf-8"))
                if data["method"] == "NotifyEvent":
                    if len(data["params"]["events"]):
                        event_type = data["params"]["events"][0]["event"]
                        # Doesn't matter what kind of button event, we accept all
                        if event_type == "single_push" or event_type == "long_push" or event_type == "double_push":
                            if self.heating_request_callback:
                                self.heating_request_callback(room_name)
            
        
    def request_status_update(self,r_name):
        mi = self.client.publish(self.topic_base+"/"+r_name+"/command", "status_update")
        mi.wait_for_publish()
        
    def request_switch_ctrl(self,r_name,status):
        cmd = "on" if status else "off"
        mi = self.client.publish(self.topic_base+"/"+r_name+"/command/switch:0", cmd)
        mi.wait_for_publish()
        
