from machine import Pin
import machine
import time, json

"""
    Driver for discrete outputs (DO)
    Config parameters are:
    "do":
        {
            "<channel name>":
            {
                "pin_num": <gpio number>,
                "state": <state>
            }
        }

   <channel name>{string} - is name which wil be shown in mqtt topic path [mandatory]
   <gpio num>{int}}  - is number of input pin [mandatory]
   <state>{int/bool}  - Init state of output pin [optional - default = false]

   Mqtt messages:
   Messages ale in form of json. Value of pin could be changed in topic "<base_topic>/do/<channel name>/set_state".
   Format of this message have to be in form "{ "state": <state>{int/bool}}".
   When value is changed or recieved message is not correct, driver publish in "<base_topic>/do/<channel name>/get_state" message in form "{ "state": <state>{int/bool}}".
"""

def build(mqtt_manager, base_path, periphs_in, loop_task, dict_in):
        dos = []
        for name, params in dict_in.items():
            try:
                sub = base_path + "do/" + name + "/set_state"
                pub = base_path + "do/" + name + "/get_state"
                state = False
                if "state" in params:
                    state = bool(params["state"])
                p = {"name": name, "inst": drvDO(params["pin_num"], mqtt_manager, sub, pub, state), "sub": sub, "pub": pub, "params": params}
                dos.append(p)
            except Exception as e:
                print("Building do: " + name + " was wrong: " + str(e))
        return dos

class drvDO:
    def __init__(self, pin_num, mqtt_manager, sub_topic, pub_topic, state):
        self.mqtt = mqtt_manager
        self.sub_topic = sub_topic
        self.pub_topic = pub_topic

        self.pin = Pin(pin_num, Pin.OUT)
        self.pin_state = bool(state)
        self.pin.value(self.pin_state)
        self.pub_cb()

        self.mqtt.register_sub_cb(self.sub_topic, self.sub_cb)
        self.mqtt.register_pub_cb(self.pub_cb)

    def sub_cb(self, topic, mess):
        try:
            messj = json.loads(mess)
            self.pin_state = bool(messj["state"])
            self.pin.value(self.pin_state)
        except Exception as e:
            print("drvDO Sub message error: " + str(e))
        self.pub_cb()

    def pub_cb(self):
        try:
            msg = json.dumps({"state": bool(self.pin_state)})
            self.mqtt.publish(self.pub_topic, msg)
        except Exception as e:
            print("drvDO Pub error: " + str(e))

