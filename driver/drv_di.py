from machine import Pin
import machine
import time, json

"""
    Driver for discrete inputs (DI)
    Config parameters are:
    "di":
        {
            "<channel name>":
            {
                "pin_num": <gpio number>,
                "settle_ms": <debounce time>
            }
        }

   <channel name>{string} - is name which wil be shown in mqtt topic path [mandatory]
   <gpio num>{int}}  - is number of input pin [mandatory]
   <debounce time>{int}  - Real debounce time is 2x <debounce time> [optional - default = 150]

   Mqtt messages:
   Messages ale in form of json. When publish something in topic "<base_topic>/di/<channel name>/que_state" (doesn't matter what)
   or pin <gpio number> changes,
   this driver rpublish in "<base_topic>/di/<channel name>/get_state" message in format "{"state": <state>{bool} }"

"""

def build(mqtt_manager, base_path, dict_in):
        dis = []
        for name, params in dict_in.items():
            try:
                sub = base_path + "di/" + name + "/que_state"
                pub = base_path + "di/" + name + "/get_state"
                settle_ms = 150
                if "settle_ms" in params:
                    settle_ms = params["settle_ms"]
                p = {"name": name, "inst": drvDI(params["pin_num"], mqtt_manager, sub, pub, settle_ms), "sub": sub, "pub": pub, "params": params}
                dis.append(p)
            except Exception as e:
                print("Building di: " + name + " was wrong: " + str(e))
        return dis

class drvDI:
    def __init__(self, pin_num, mqtt_manager, sub_topic, pub_topic, settle_ms=150):
        self.mqtt = mqtt_manager
        self.sub_topic = sub_topic
        self.pub_topic = pub_topic

        self.settle_ms = settle_ms
        self.old_time = time.ticks_ms()
        self.pin = Pin(pin_num, Pin.IN, pull=Pin.PULL_UP)
        self.pin.irq(self.irq_cb, trigger=(Pin.IRQ_RISING or Pin.IRQ_FALLING))
        self.pub_cb()
        self.scheduled_time=time.ticks_ms() + self.settle_ms

        self.mqtt.register_sub_cb(self.sub_topic, self.sub_cb)
        self.mqtt.register_pub_cb(self.pub_cb)

    def irq_cb(self, a):
        if time.ticks_diff(self.scheduled_time, time.ticks_ms()) < 0:
            time.sleep_ms(self.settle_ms)
            self.pub_cb()
            self.scheduled_time=time.ticks_ms() + self.settle_ms

    def sub_cb(self, topic, mess):
        self.pub_cb()

    def pub_cb(self):
        try:
            msg = json.dumps({"state": bool(self.pin.value())})
            self.mqtt.publish(self.pub_topic, msg)
        except Exception as e:
            print("drvDI Pub error: " + str(e))

