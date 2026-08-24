import time

from umqtt.simple import MQTTClient

SOUSCRIPTIONS = {
    # Températures
    "home/temp/dehors": "_dehors",
    "home/temp/buandrie": "buandrie",
    "home/temp/bureau": "bureau",
    "home/temp/cuisine": "cuisine",
    "home/temp/cyril": "cyril",
    "home/temp/douche": "douche",
    "home/temp/parent": "parents",
    "home/temp/salon": "salon",
    # Humidité
    "home/humidity/dehors": "_dehors",
    "home/humidity/buandrie": "buandrie",
    "home/humidity/bureau": "bureau",
    "home/humidity/cuisine": "cuisine",
    "home/humidity/cyril": "cyril",
    "home/humidity/douche": "douche",
    "home/humidity/parent": "parents",
    "home/humidity/salon": "salon",
    # IUnterrupteurs
    "home/switch/ventilo": "Ventilo",
    "home/switch/pipmcnet": "RPi",
    "home/switch/sapin": "Buandrie",
    "home/switch/multimedia": "Multimédia",
    "home/switch/cuisine": "Cuisine",
    "home/switch/douche": "Douche",
}


class MQTT:
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

    def disconnect(self):
        self.client.disconnect()

    def set_callback(self, fct):
        self.callbacks.append(fct)

    def mqtt_callback(self, topic, msg):
        # message_string = msg.decode('utf-8')  # Decode the MQTT message
        topic = topic.decode()
        msg = msg.decode('utf-8')
        # print(f"Received message on topic {topic}: {msg}")
        for fct in self.callbacks:
            try:
                fct(topic, msg)
            except Exception as e:
                print(f"Erreur mqtt_callback() : {e} ({topic}, {msg})")

    def get_room(self, topic):
        return SOUSCRIPTIONS[topic]

    def check_msg(self):
        try:
            self.client.check_msg()
        except OSError:
            print("Déconnexion MQTT")
            self.connect()
        except Exception as e:
            print(f"Error while waiting for MQTT messages: {e}")
