# iot-mqtt-stack
Simple framework for easy creation of MQT comunicating IoT units.

With this framework you can easily create simple devices comucating over mqtt. For a siple devices (like a digital inputs/outputs, pwm outputs...) you only write config file and you are done.
This framework is mainly developed for ESP32 boards with micropython and it uses umqtt.robust2 lib [\[Here\]](https://github.com/fizista/micropython-umqtt.robust2) and [\[Here\]](https://pypi.org/project/micropython-umqtt.robust2/)
You can install this lib directly in ESP32 in micropython:

    import upip
    upip.install("micropython-umqtt.robust2")

## How to use
When you want to use this framework, just install umqtt.robust2 lib to your board, copy files in this repo and write config file "unitconf.json". This config is plain json file. Example with comments - this config does not work, you need to remove coments - is [\[Here\]](https://github.com/Selmacas/iot-mqtt-stack/blob/master/unitconf_comented_example.json). Mqtt path is build as __\<base mqtt path\>/\<driver\>/\<name of channel\>\< driver dependant \>__
So for config in form


    {
        "unit_id": "<unique unit id>", #It is mandatory that this id is unique!!!
        "mqtt":
        {
            "broker_ip": "<broker_address>",
            "base_topic": "<base mqtt path>",
            "wifi_ssid": "<SSID>",
            "wifi_pass": "<PASSWD>"
        },
        "peripherals":
        {
            "do":
            {
                "ch1":
                {
                    "pin_num": 14,
                    "state": false
                }
            },
        }

    }

the path is __"\<base mqtt path\>/do/ch1/set\_state"__ or  __"\<base mqtt path\>/do/ch1/set\_state"__, _"set_state"_ or _"get_state"_ are described directly in driver and are driver dependant. Also format of mqtt messages are driver dependant. Format of shis messages are described directly in source foles of drivers in /driver/ folder.

# How to write driver

