
import network, gc, json
from mqttmanager import mqttmanager
from builtins import Exception

class mqttUnitException(Exception):
    pass


class mqttUnit:
    def __init__(self, config):
        self.config_file = config
        self.config_tree = None
        self.wifi = None
        self.mqtt_manager = None
        self.peripherals = {}

        self.unit_id = None
        self.base_topic = None

        self.is_running = False

    def run(self):
        if self.is_running == True:
            print("MqttUnit \"" + self.unit_id + "\" is running!\n\n")
            return

        print("\n\nStarting mqttUnit ...")
        gc.enable()
        try:
            self.__build_config_tree()
            self.__connect_wifi()
            self.__create_mqtt_manager()
            self.__build_peripherals()
        except Exception as e:
            print("Somethig went wrong: " + str(e))
            return
        self.is_running = True
        print("MqttUnit \"" + self.unit_id + "\" is now running!\n\n")

    def __build_config_tree(self):
        print("Loading config: \"" + self.config_file + "\" ...")
        try:
            f = open(self.config_file, "r")
        except Exception as e :
            print("Can not open \"" + self.config_file + "\": " + str(e))
            raise mqttUnitException

        try:
            self.config_tree = json.load(f)
        except Exception as e :
            print("Can not load config: " + str(e))
            f.close()
            raise mqttUnitException
        f.close()
        print("Config \"" + self.config_file + "\" was loaded")

    def __connect_wifi(self):
        print("Starting WiFi ...")
        try:
            ssid = self.config_tree["mqtt"]["wifi_ssid"]
            passwd = self.config_tree["mqtt"]["wifi_pass"]
        except Exception as e:
            print("Can not read WiFi config: " + str(e))
            raise mqttUnitException
        try:
            self.wifi = network.WLAN(network.STA_IF)
            self.wifi.active(True)
            self.wifi.connect(ssid, passwd)
            while not self.wifi.isconnected():
                pass
        except Exception as e:
            print("Can not connect WiFi: " + str(e))
            raise mqttUnitException
        print("WiFi is running: " + str(self.wifi.ifconfig()) )

    def __create_mqtt_manager(self):
        print("Starting MQTT ...")
        try:
            self.unit_id = self.config_tree["unit_id"]
            broker_ip = self.config_tree["mqtt"]["broker_ip"]
            self.base_topic = self.config_tree["mqtt"]["base_topic"]
        except Exception as e:
            print("Can not read MQTT config: " + str(e))
            raise mqttUnitException
        try:
            self.mqtt_manager = mqttmanager(self.unit_id, broker_ip, 200)
        except Exception as e:
            print("Can not create MQTT manager: " + str(e))
            raise mqttUnitException
        print("MQTT ip: " + broker_ip)
        print("MQTT base topic: " + self.base_topic)
        print("MQTT is running")


    def __build_peripherals(self):
        print("Buiding peripherals tree ...")
        peripherals_c = self.config_tree["peripherals"]
        for periph in peripherals_c:
            try:
                mod = __import__("driver.drv_" + periph)
                drv = getattr(mod, "drv_" + periph)
                #print("==> " + str(periph) + ": " + str(peripherals_c[periph]))
                self.peripherals[periph] = drv.build(self.mqtt_manager, self.base_topic, peripherals_c[periph])
            except Exception as E:
                print("Can not build \"" + periph +  "\": " + str(E))
        self.__print_peripherals_tree()
        print("Peripherals was initialized.")


    def __print_peripherals_tree(self):
        print("Peripherals tree is:")
        for perip, value in self.peripherals.items():
            print(perip + ":" )
            for i in value:
                try:
                    print("    " + i["name"] + ":")
                    print("        Subscribe topic: " + i["sub"])
                    print("        Publish topic  : " + i["pub"])
                    if "params" in i:
                        print("        Parameters     : " + str(i["params"]))
                except Exceptions as e:
                    print("Something is wrong: " + str(e))

