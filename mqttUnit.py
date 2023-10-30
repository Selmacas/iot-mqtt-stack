
import network, gc, json
import webrepl
import machine
from machine import I2C, SPI, UART, Pin, Timer
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
        self.i_peripherals = {"i2c": [{"i2c": None, "lock": False},{"i2c": None, "lock": False}], "spi": [{"spi": None, "lock": False},{"spi": None, "lock": False}], "uart": [{"uart": None, "lock": False},{"uart": None, "lock": False}, {"uart": None, "lock": False}]}

        self.loop_tasks=[]
        self.unit_id = None
        self.base_topic = None
        self.pub_topic_end = "system/response"

        self.is_running = False
        self.debug = False
        
        self.timer = Timer(0)
        self.counter = 0
        

    def start(self):
        if self.is_running == True:
            print("MqttUnit \"" + self.unit_id + "\" is running!\n\n")
            return

        print("\n\nStarting mqttUnit ...")
        gc.enable()
        try:
            self.__build_config_tree()
            self.__connect_wifi()
            self.__create_mqtt_manager()
            self.__build_internl_peripherals()
            self.__build_peripherals()
        except Exception as e:
            print("Somethig went wrong in start: " + str(e))
            return
        self.is_running = True
        print("MqttUnit \"" + self.unit_id + "\" is now running!")
        if self.debug:
            print("DEBUG MODE\n\n")
        else:
            print("\n\n")

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
        if "debug" in self.config_tree:
            self.debug = bool(self.config_tree["debug"])
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
            self.mqtt_manager = mqttmanager(self.unit_id, broker_ip)
            self.timer.init(period=10, mode=Timer.PERIODIC, callback=self.timer_cb)
        except Exception as e:
            print("Can not create MQTT manager: " + str(e))
            raise mqttUnitException
        try:   
            self.mqtt_manager.register_sub_cb(self.base_topic + "system/cmd", self.__system_cb)
        except Exception as e:
            print("Can not register system topic: " + str(e))
            raise mqttUnitException
        print("MQTT ip: " + broker_ip)
        print("MQTT base topic: " + self.base_topic)
        print("MQTT is running")
        
    def __build_internl_peripherals(self):
        print("Buiding internal (shared) peripherals tree ...")
        peripherals_c = self.config_tree["internal_peripherals"]
        for p in peripherals_c:
            periph = peripherals_c[p]
            try:
                if p.lower().startswith("i2c"):
                    if periph["num"] in range(2):
                        self.i_peripherals["i2c"][periph["num"]]["i2c"] = I2C(periph["num"], sda=Pin(periph["sda"]), scl=Pin(periph["scl"]), freq=periph["freq"], timeout=100)
                        self.i_peripherals["i2c"][periph["num"]]["lock"] = False    
                elif p.lower().startswith("spi"):
                    if periph["num"] in range(2):
                        self.i_peripherals["spi"][periph["num"]]["spi"] = SPI(periph["num"], baudrate=periph["freq"], sck=Pin(periph["sck"]), mosi=Pin(periph["mosi"]), miso=Pin(periph["mosi"]))
                        self.i_peripherals["spi"][periph["num"]]["lock"] = False
                elif p.lower().startswith("uart"):
                    if periph["num"] in range(1,3):
                        self.i_peripherals["uart"][periph["num"]]["uart"] = UART(periph["num"], baudrate=periph["baudrate"], tx=Pin(periph["tx"]), rx=Pin(periph["rx"]))
                        self.i_peripherals["uart"][periph["num"]]["lock"] = False     
            except Exception as E:
                print("Can not build \"" + periph +  "\": " + str(E))
        self.__print_internal_peripherals_tree()
        print("Internal peripherals was initialized.\n")


    def __build_peripherals(self):
        print("Buiding peripherals tree ...")
        peripherals_c = self.config_tree["peripherals"]
        for periph in peripherals_c:
            try:
                mod = __import__("driver.drv_" + periph)
                drv = getattr(mod, "drv_" + periph)
                #print("==> " + str(periph) + ": " + str(peripherals_c[periph]))
                self.peripherals[periph] = drv.build(self.mqtt_manager, self.base_topic, self.i_peripherals, self.loop_tasks, peripherals_c[periph])
            except Exception as E:
                print("Can not build \"" + periph +  "\": " + str(E))
        self.__print_peripherals_tree()
        print("Peripherals was initialized.\n")


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
                    print("Something is wrong in print peripherals tree: " + str(e))
                    
    def __print_internal_peripherals_tree(self):
        print("Internal peripherals tree is:")
        for perip, value in self.i_peripherals.items():
            print(perip + ":" )
            for i in value:
                try:
                    print("    " + str(i))
                except Exceptions as e:
                    print("Something is wrong in print internal peripherals tree: " + str(e))

    def __system_cb(self, topic, mess):
        try:
            messj = json.loads(mess)
            #potentialy hazardeous command which are enabled only in debug mode (set from unitconf.json)
            if self.debug == True: 
                if "webrepl" in messj:              
                    self.enable_webrepl = bool(messj["webrepl"])
                    if self.enable_webrepl:
                        webrepl.start()
                        print("system: webrepl started")
                    else:
                        webrepl.stop()
                        print("system: webrepl stopped")
                if "reset" in messj:
                    if bool(messj["reset"]):
                        print("system: Reset from mqtt!!")
                        machine.reset()
                    
            #safe system commands       
            if "ip" in messj:           
                ip = self.wifi.ifconfig()
                msg = json.dumps({"ip": ip[0], "netmask": ip[1], "gateway": ip[2], "dns": ip[3] })
                self.mqtt_manager.publish(self.base_topic + self.pub_topic_end , msg)
           
        except Exception as e:
            print("System sub message error: " + str(e))    
            
    def timer_cb(self, a): # called every 10ms
        self.counter += 1
        if self.counter > 100000:
            self.counter = 0

        if (self.counter % 10) == 0: # call mqtt manager every 100ms
            self.mqtt_manager.periodic_cb()
        
        for task in self.loop_tasks:
            task()
            
