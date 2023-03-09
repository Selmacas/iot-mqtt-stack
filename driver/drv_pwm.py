from machine import Pin, PWM
import time, json

"""
    Driver for PWM outputs (PWM)
    Config parameters are:
    "pwm":
        {
            "<channel name>":
            {
                "pin_num": <gpio number>,
                "freq": <frequency>,
                "duty": <duty>
            }
        }

   <channel name>{string} - is name which wil be shown in mqtt topic path [mandatory]
   <gpio num>{int}}  - is number of input pin [mandatory]
   <frequency>{int}  - Frequency od pwm in Hz [optional - default = 1000]
   <duty>{int 0-100} - Initial duty of this channel in % [optional - default = 0]

   Mqtt messages:
   Messages ale in form of json. Value of pin could be changed in topic "<base_topic>/pwm/<channel name>/set_duty".
   Format of this message have to be in form "{ "duty": <duty>{int}}", duty is int in range 0 - 100.
   When value is changed, driver publish in "<base_topic>/pwm/<channel name>/get_state" message in form "{ "duty": <duty>{int}}".
"""

def build(mqtt_manager, base_path, dict_in):
        pwms = []
        for name, params in dict_in.items():
            try:
                sub = base_path + "pwm/" + name + "/set_duty"
                pub = base_path + "pwm/" + name + "/get_duty"
                duty = 0
                freq = 1000
                if "duty" in params:
                    duty = params["duty"]
                if "freq" in params:
                    freq = params["freq"]
                p = {"name": name, "inst": dPWM(params["pin_num"], mqtt_manager, sub, pub, freq, duty), "sub": sub, "pub": pub, "params": params}
                pwms.append(p)
            except:
                print("Building pwm: " + name + " was wrong: " + str(e))
        return pwms

class dPWM:
    def __init__(self, pin_num, mqtt_manager, sub_topic, pub_topic, freq=1000, duty=0):
        self.pwm = PWM(Pin(pin_num))

        self.pwm.duty_u16(int(duty*65535/100))
        self.pwm.freq(freq)
        self.mqtt = mqtt_manager
        self.sub_topic = sub_topic
        self.pub_topic = pub_topic

        self.mqtt.register_sub_cb(self.sub_topic, self.sub_cb)
        self.mqtt.register_pub_cb(self.pub_cb)
        time.sleep_ms(1)
        self.pub_cb()

    def sub_cb(self, topic, mess):
        try:
            messj = json.loads(mess)
            duty = int(messj["duty"])
            if duty <= 100:
                self.pwm.duty_u16(int(duty*65535/100))
                time.sleep_ms(1)
            print(self.pwm)
            self.pub_cb()
        except Exception as e:
            print("drvPWM Sub error: " + str(e))

    def pub_cb(self):
        msg = json.dumps({"duty": int(round(self.pwm.duty_u16()*100/65535))})
        try:
            self.mqtt.publish(self.pub_topic, msg)
        except Exception as e:
            print("drvPWM Pub error: " + str(e))
