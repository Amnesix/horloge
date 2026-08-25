import time

from umqtt.simple import MQTTClient

from myapp.utils import Color, Page, verifier_connexion

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
    # Interrupteurs
    "home/switch/ventilo": "Ventilo",
    "home/switch/pipmcnet": "RPi",
    "home/switch/sapin": "Buandrie",
    "home/switch/multimedia": "Multimédia",
    "home/switch/cuisine": "Cuisine",
    "home/switch/douche": "Douche",
    # Tests
    "home/commandes": "-"
}

TOPIC_MSG = {
    "RPi": "home/toggle/rpi",
    "Douche": "home/toggle/douche",
    "Cuisine": "home/toggle/cuisine",
    "Ventilo": "home/toggle/ventilo",
    "Buandrie": "home/toggle/buandrie",
    "Multimédia": "home/toggle/multimedia",
}


class MQTT:
    callbacks = []

    def __init__(self, broker, port, loggin):
        self.client_id = f"MQTT-HA-{time.time() % 10**6}"
        self.client = MQTTClient(self.client_id, broker, port=port)
        self.client.set_callback(self.mqtt_callback)
        self.set_callback(self.mqtt_commandes)
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

    def send_msg(self, what, msg):
        print(f"Send {what}: {TOPIC_MSG[what]}:'{msg}'")
        try:
            self.client.publish(TOPIC_MSG[what], msg)
        except KeyError:
            print(f"Erreur de clé send_msg({what}, {msg})")

    def set_callback(self, fct):
        self.callbacks.append(fct)

    def remove_callback(self, fct):
        self.callbacks.remove(fct)

    def mqtt_callback(self, topic, msg):
        # message_string = msg.decode('utf-8')  # Decode the MQTT message
        topic = topic.decode()
        msg = msg.decode('utf-8')
        print(f"Received message on topic {topic}: {msg}")
        for fct in self.callbacks:
            try:
                fct(topic, msg)
            except Exception as e:
                print(f"Erreur mqtt_callback() : {e} ({topic}, {msg})")

    def mqtt_commandes(self, topic, msg):
        if 'command' in topic and msg in ('calendrier', 'flip', 'switches',
                                          'temperatures', 'tests', 'exit',
                                          'horloge'):
            Page.set_page(msg)

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


class MQTTLog:

    def __init__(self, presto, display, vector, touch, mqtt, loggin):
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        self.mqtt = mqtt
        self.loggin = loggin
        self.display.set_pen(Color.BLACK)  # Black background
        self.display.clear()
        self.presto.update()

    def cb(self, topic, msg):
        self.loggin.log(f"Reception : {topic} / {msg}")

    def affiche(self):
        print("Enter tests")
        self.mqtt.set_callback(self.cb)
        while True:
            verifier_connexion(self.presto, self.loggin)
            self.mqtt.check_msg()
            if Page.page != 'tests':
                self.mqtt.remove_callback(self.cb)
                return
            try:
                # Wait for MQTT messages (non-blocking check)
                self.mqtt.check_msg()

            except Exception as e:
                print(f"Error while waiting for MQTT messages: {e}")

            time.sleep(.5)
