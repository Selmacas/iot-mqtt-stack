from machine import Pin, PWM
import math, time, json

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
                "natural": <natural>
            }
        }

   <channel name>{string} - is name which wil be shown in mqtt topic path [mandatory]
   <gpio num>{int}}  - is number of input pin [mandatory]
   <frequency>{int}  - Frequency od pwm in Hz [optional - default = 1000]
   <duty>{int 0-100} - Initial duty of this channel in % [optional - default = 0]
   <natural>{bool}   - False = linear PWM to duty (duty 50 ~ 50% of power/duty time), True = optimized for driving LED strips (duty 50 ~ leds light on 50% of intensity, but power !=50% )

   Mqtt messages:
   Messages are in form of json. Value of pin could be changed in topic "<base_topic>/pwm/<channel name>/set_duty".
   Format of this message have to be in form "{ "duty": <duty>{int}}", duty is int in range 0 - 100.
   When value is changed or recieved message is not correct, driver publish in "<base_topic>/pwm/<channel name>/get_state" message in form "{ "duty": <duty>{int}}".
"""

def build(mqtt_manager, base_path, periphs_in, loop_task, dict_in):
        pwms = []
        for name, params in dict_in.items():
            try:
                sub = base_path + "pwm/" + name + "/set_duty"
                pub = base_path + "pwm/" + name + "/get_duty"
                duty = 0
                freq = 1000
                natural = False
                if "duty" in params:
                    duty = params["duty"]
                if "freq" in params:
                    freq = params["freq"]
                if "natural" in params:
                    natural = params["natural"] != False
                
                iPWM = dPWM(params["pin_num"], mqtt_manager, sub, pub, freq, duty, natural)
                p = {"name": name, "inst": iPWM, "sub": sub, "pub": pub, "params": params}
                pwms.append(p)
            except:
                print("Building pwm: " + name + " was wrong: " + str(e))
        return pwms

class dPWM:
    def __init__(self, pin_num, mqtt_manager, sub_topic, pub_topic, freq=1000, duty=0, natural=False):
        self.pwm = PWM(Pin(pin_num))
        self.natural = natural
        self.r = 10 # Calcualted according: https://diarmuid.ie/blog/pwm-exponential-led-fading-on-arduino-or-other-platforms ; m=100, p=1024

        duty_i = int((duty*1023/100, 2**(duty/self.r)-1)[self.natural]);
        self.pwm.duty(duty_i)
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
            if duty <= 100 && duty >= 0:
                duty_i = int((duty*1023/100, 2**(duty/self.r)-1)[self.natural])
                self.pwm.duty(duty_i)
                time.sleep_ms(1)
                #print("duty: " + str(duty) + " duty_i: " + str(duty_i) + " pwm: " + str(self.pwm))
        except Exception as e:
            print("drvPWM Sub error: " + str(e))
        self.pub_cb()

    def pub_cb(self):
        try:
            duty = self.pwm.duty()
            duty_i = int(round( (duty*100/1023, self.r*math.log(duty+1)/math.log(2))[self.natural] ))
            msg = json.dumps({"duty": duty_i})
            self.mqtt.publish(self.pub_topic, msg)
        except Exception as e:
            print("drvPWM Pub error: " + str(e))
