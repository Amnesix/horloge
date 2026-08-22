import time

from umqtt.simple import MQTTClient

SOUSCRIPTIONS = {
    # Températures
    "home/temps/dehors": "_dehors",
    "home/temp/buandrie": "buandrie",
    "home/temp/bureau": "bureau",
    "home/temp/cuisine": "cuisine",
    "home/temp/cyril": "cyril",
    "home/temps/diane": "diane",
    "home/temps/parent": "parents",
    "home/temp/salon": "salon",
    # IUnterrupteurs
    "home/switch/ventilo": "Ventilo",
    "home/switch/pipmcnet": "RPi",
    "home/switch/sapin": "Buandrie",
    "home/switch/multimedia": "Multimédia",
    "home/switch/cuisine": "Cuisine",
    "home/switch/douche": "Douche",
}


class MQTT:
    """ Je ne comprend pas pourquoi, mais avec la classe cela ne fonctionne pas"""
    callbacks = []

    def __init__(self, broker, port, loggin):
        self.client_id = f"MQTT-HA-{time.time() % 10**6}"
        self.client = MQTTClient(self.client_id, broker, port=port)
        self.client.set_callback(self.mqtt_callback)
        self.connect()
        loggin.log(f"Connected to MQTT at {broker}.")

    def connect(self):
        try:
            self.client.connect()
            for k in SOUSCRIPTIONS:
                self.client.subscribe(k)
        except OSError as e:
            print(f"Erreur de connexion : {e}")

    def set_callback(self, fct):
        self.callbacks.append(fct)

    def mqtt_callback(self, topic, msg):
        # message_string = msg.decode('utf-8')  # Decode the MQTT message
        topic = SOUSCRIPTIONS[topic.decode()]
        msg = msg.decode('utf-8')
        # print(f"Received message on topic {topic}: {msg}")
        for fct in self.callbacks:
            try:
                fct(topic, msg)
            except Exception as e:
                print(f"Erreur mqtt_callback() : {e} ({topic}, {msg})")

    def check_msg(self):
        try:
            self.client.check_msg()
        except OSError:
            print("Déconnexion MQTT")
            self.connec()
        except Exception as e:
            print(f"Error while waiting for MQTT messages: {e}")
