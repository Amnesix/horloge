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

loggin = None
callbacks = []


def set_callback(fct):
    global callbacks
    callbacks.append(fct)


def mqtt_callback(topic, msg):
    # message_string = msg.decode('utf-8')  # Decode the MQTT message
    global callbacks
    topic = SOUSCRIPTIONS[topic.decode()]
    msg = msg.decode('utf-8')
    # print(f"Received message on topic {topic}: {msg}")
    for fct in callbacks:
        try:
            fct(topic, msg)
        except Exception as e:
            print(f"Erreur mqtt_callback() : {e}")


def mqtt_connect(broker, port, log):
    global loggin, client
    loggin = log
    client_id = f"MQTT-HA-{time.time() % 10**6}"
    # print(f"Connexion MQTT sur {broker}:{port} ({type(broker)} {type(port)})")
    client = MQTTClient(client_id, broker, port=port)
    client.set_callback(mqtt_callback)
    try:
        client.connect()
        loggin.log(f"Connected to MQTT at {broker}.")
    except Exception as e:
        loggin.log(f"MQTT: Connexion erreur {e}")
        print(f"MQTT: Connexion erreur {e}")
    for k in SOUSCRIPTIONS:
        client.subscribe(k)


def check_msg():
    try:
        # Wait for MQTT messages (non-blocking check)
        client.check_msg()

    except Exception as e:
        print(f"Error while waiting for MQTT messages: {e}")


class MQTT:
    """ Je ne comprend pas pourquoi, mais avec la classe cela ne fonctionne pas"""

    def __init__(self, broker, port, loggin):
        self.client_id = f"MQTT-HA-{time.time() % 10**6}"
        self.client = MQTTClient(self.client_id, broker, port=port)
        self.client.set_callback(mqtt_callback)
        try:
            self.client.connect()
            loggin.log(f"Connected to MQTT at {broker}.")
        except Exception as e:
            loggin.log(f"MQTT: Connexion erreur {e}")
            print(f"MQTT: Connexion erreur {e}")
        for k in SOUSCRIPTIONS:
            client.subscribe(k)

    def mqtt_callback(self, topic, msg):
        message_string = msg.decode('utf-8')  # Decode the MQTT message
        print(f"Received message on topic {topic.decode()}: {message_string}")

    def check_msg(self):
        try:
            self.client.check_msg()

        except Exception as e:
            print(f"Error while waiting for MQTT messages: {e}")
