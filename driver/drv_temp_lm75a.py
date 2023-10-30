import struct
from machine import I2C
import time, json

def build(mqtt_manager, base_path, periphs_in, loop_task, dict_in):
        dis = []
        for name, params in dict_in.items():
            try:
                sub = base_path + "therm/" + name + "/que"
                pub = base_path + "therm/" + name + "/get"
                i2c = periphs_in["i2c"][params["i2c"]]["i2c"]
                t = drvT(i2c, params["addr"], mqtt_manager, sub, pub)
                p = {"name": name, "inst": t, "sub": sub, "pub": pub, "params": params}
                dis.append(p)
            except Exception as e:
                print("Building temperature lm75a: " + name + " was wrong: " + str(e))
        return dis


class drvT:
    def __init__(self, i2c, addr, mqtt_manager, sub_topic, pub_topic):
        self.mqtt = mqtt_manager
        self.sub_topic = sub_topic
        self.pub_topic = pub_topic
        self.i2c = i2c
        self.addr = addr
        self.raw =  self.i2c.readfrom_mem(self.addr, 0, 2)
        self.t = struct.unpack(">h", self.raw)[0]/256.0
        self.pub_cb()
        
        self.mqtt.register_sub_cb(self.sub_topic, self.sub_cb)
        self.mqtt.register_pub_cb(self.pub_cb)
        
    def pub_cb(self):
        try:
            self.raw =  self.i2c.readfrom_mem(self.addr, 0, 2)
            self.t = struct.unpack(">h", self.raw)[0]/256.0
            msg = json.dumps({"temperature": self.t})
            self.mqtt.publish(self.pub_topic, msg)
        except Exception as e:
            print("drvT Pub error: " + str(e))
    
    
    def sub_cb(self, topic, mess):
        self.pub_cb()


