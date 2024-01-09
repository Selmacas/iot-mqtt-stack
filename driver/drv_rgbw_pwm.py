from machine import Pin, PWM
import math, time, json

"""
    Driver for RGBW PWM outputs
    Config parameters are:
    "rgbw_pwm":
        {
            "<channel name>":
            {
                "R": <gpio number>,
                "G": <gpio number>,
                "B": <gpio number>,
                "W": <gpio number>,
                "freq": <frequency>,
            }
        }

   <channel name>{string} - is name which wil be shown in mqtt topic path [mandatory]
   <R>{int}}  - is number of input pin [optional]
   <G>{int}}  - is number of input pin [optional]
   <B>{int}}  - is number of input pin [optional]
   <W>{int}}  - is number of input pin [optional]
   <frequency>{int}  - Frequency od pwm in Hz [optional - default = 1000]

   Mqtt messages:
   Messages are in form of json. Value of pin could be changed in topic "<base_topic>/pwm/<channel name>/set_duty".
   Format of this message have to be in form "{ "duty": <duty>{int}}", duty is int in range 0 - 100.
   When value is changed or recieved message is not correct, driver publish in "<base_topic>/pwm/<channel name>/get_state" message in form "{ "duty": <duty>{int}}".
"""

def build(mqtt_manager, base_path, periphs_in, loop_task, dict_in):
        pwms = []
        for name, params in dict_in.items():
            try:
                sub = base_path + "rgbw_pwm/" + name + "/set_duty"
                pub = base_path + "rgbw_pwm/" + name + "/get_duty"
                freq = 1000
                LED_pins = {"R": None, "G": None, "B": None, "W": None}
                for led in LED_pins.keys():
                    if led in params:
                        LED_pins[led] = int(params[led])
                if "freq" in params:
                    freq = params["freq"]
                
                iRGBW_PWM = dRGBW_PWM(LED_pins, mqtt_manager, sub, pub, freq)
                p = {"name": name, "inst": iRGBW_PWM, "sub": sub, "pub": pub, "params": params}
                pwms.append(p)
            except Exception as e:
                print("Building pwm: " + name + " was wrong: " + str(e))
        return pwms

class dRGBW_PWM:
    def __init__(self, led_pins, mqtt_manager, sub_topic, pub_topic, freq=1000):
        self.led_pwms = {"R": None, "G": None, "B": None, "W": None}
        for led in self.led_pwms.keys():
            if led in led_pins:
                self.led_pwms[led] = PWM(Pin(led_pins[led]))
                self.led_pwms[led].duty(0)
                self.led_pwms[led].freq(freq)

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
            for led in self.led_pwms.keys():
                if led in messj:
                    duty = int(messj[led])
                    if duty <= 100 and duty >= 0:
                        duty_i = int(duty * 1023 / 100)
                        self.led_pwms[led].duty(duty_i)
                        time.sleep_ms(1)
                        #print("duty: " + str(duty) + " duty_i: " + str(duty_i) + " pwm: " + str(self.led_pwms[led]))
        except Exception as e:
            print("drvPWM Sub error: " + str(e))
        self.pub_cb()

    def pub_cb(self):
        try:
            msg_i = {"R": None, "G": None, "B": None, "W": None}
            for led in self.led_pwms.keys():
                if self.led_pwms[led] != None:
                    duty = self.led_pwms[led].duty()
                    msg_i[led] = int(round(duty*100/1023))
                    time.sleep_ms(1)
            msg = json.dumps(msg_i)
            self.mqtt.publish(self.pub_topic, msg)
        except Exception as e:
            print("drvPWM Pub error: " + str(e))
