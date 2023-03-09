from machine import Timer
from lib.umqtt.robust2 import MQTTClient

class mqttmanager:
    def __init__(self, unit_id, broker_ip, loop_period_ms=200):
        self.topics = {}
        self.pub_cbs =[]
        self.mqtt = MQTTClient(unit_id, broker_ip)
        self.mqtt.NO_QUEUE_DUPS = True
        self.mqtt.MSG_QUEUE_MAX = 2
        self.mqtt.set_callback(self.eval_mqtt)
        self.mqtt.connect(clean_session=True)
        self.timer = Timer(0)
        self.timer.init(period=loop_period_ms, mode=Timer.PERIODIC, callback=self.timer_cb)

    def register_sub_cb(self, topic, callback):
        self.mqtt.subscribe(topic.encode("utf-8"))
        if topic in self.topics.keys():
            self.topics[topic].append(callback)
        else:
            self.topics[topic] = [callback]

    def register_pub_cb(self, callback):
        self.pub_cbs.append(callback)

    def eval_mqtt(self, topic, mes, retained, duplicat):
        try:
            for fcn in self.topics[str(topic, "utf-8")]:
                fcn(str(topic, "utf-8"), str(mes, "utf-8"))
        except Exception as e:
            print("For this topic callback is not rgistered: " + str(e) )

    def publish(self, topic, msg):
        self.mqtt.publish(topic.encode("utf-8"), msg.encode("utf-8"), retain=True, qos=1)

    def timer_cb(self, a):
        if self.mqtt.is_conn_issue():
            if self.mqtt.is_conn_issue():
                self.mqtt.reconnect()
            else:
                self.mqtt.resubscribe()
        else:
            self.mqtt.check_msg() # needed when publish(qos=1), ping(), subscribe()
            self.mqtt.send_queue()  # needed when using the caching capabilities for unsent messages

