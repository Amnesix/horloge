import binascii
import time

import machine
from umqtt.simple import MQTTClient

from myapp.utils import TZ, Color, Log, Page, get_touch, verifier_connexion

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
    # Autres
    "home/commandes": "-",
    "home/alerte": "-",
    "home/alarme": "-",
    "home/debug": "print('OK, je suis là')",
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
        loggin.log("Initialisation MQTT")
        self.broker = broker
        self.port = port
        unique = str(binascii.hexlify(machine.unique_id()))
        self.client_id = f'{unique}'
        self.connect()
        loggin.log(f"Connected to MQTT at {broker}:{port}.")

    def connect(self):
        self.client = MQTTClient(self.client_id, self.broker, port=self.port)
        self.client.set_callback(self.mqtt_callback)
        self.set_callback(self.mqtt_commandes)
        try:
            self.client.connect()
            for k in SOUSCRIPTIONS:
                self.client.subscribe(k)
        except OSError as e:
            print(f"Erreur de connexion : {e}")

    def disconnect(self):
        if self.client is not None:
            self.client.disconnect()
        self.client = None

    def reconnect(self):
        print("Déconnexion client MQTT")
        if self.client is not None:
            self.client.disconnect()
        print("Connexion client MQTT")
        self.connect()

    def send_msg(self, what, msg):
        print(f"Send {what}: {TOPIC_MSG[what]}:'{msg}'")
        try:
            if self.client is not None:
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
        for fct in self.callbacks:
            try:
                fct(topic, msg)
            except Exception as e:
                print(f"Erreur mqtt_callback() : {e} ({topic}, {msg})")
                print(fct.__name__)

    def mqtt_commandes(self, topic, msg):
        if 'command' in topic:
            Page.set_page(msg)

    def get_room(self, topic):
        return SOUSCRIPTIONS[topic]

    def check_msg(self):
        try:
            if self.client is not None:
                self.client.check_msg()
        except OSError:
            print("Déconnexion MQTT")
            self.connect()
        except Exception as e:
            print(f"Error while waiting for MQTT messages: {e}")


class MQTTLog:
    nb_msg = 0

    def __init__(self, presto, display, vector, touch, mqtt, alerte, alarmes):
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        self.mqtt = mqtt
        self.alerte = alerte
        self.alarmes = alarmes
        self.loggin = Log(presto, display, vector, "Messages MQTT")
        self.start = time.time()
        self.mqtt.set_callback(self.cb)

    def cb(self, topic, msg):
        """CallBack messages MQTT"""
        t = time.time()
        _, _, _, h, m, s, _, _ = time.gmtime(t + TZ.get_offset(t) * 3600)
        if 'temp' in topic:
            color = Color.GREEN
        elif 'humidity' in topic:
            color = Color.CYAN
        else:
            color = Color.GREY
        if 'alert' in topic:
            self.alerte.alerte(msg)
        elif 'debug' in topic:
            print(exec(msg))
        elif 'alarme' in topic:
            print(f'Alarme : {msg}')
            try:
                if msg == 'list':
                    for index, al in enumerate(self.alarmes.get_alarmes()):
                        try:
                            s = f"Alarme #{index} : {al}"
                            print(s)
                            self.loggin.log(s)
                        except ValueError:
                            print(f"List alarmes ValueError : {al}")
                    return
                cmd, ha, ma, sa = msg.split()
                ha, ma, sa = map(int, (ha, ma, sa))
                if cmd == 'add':
                    self.loggin.log(
                        f"{h:02d}:{m:02d}:{s:02d} : A : ADD Alarm at {ha:d}:{ma:02d}:{sa:02d}",
                        aff=Page.get_page() == 'mqttlogs',
                        color=Color.ORANGE)
                    self.alarmes.add_alarme(ha, ma, sa)
                elif cmd == 'del':
                    self.loggin.log(
                        f"{h:02d}:{m:02d}:{s:02d} : A : DEL Alarm at {ha:2d}:{ma:02d}:{sa:02d}",
                        aff=Page.get_page() == 'mqttlogs',
                        color=Color.ORANGE)
                    for index, alarme in enumerate(self.alarmes.get_alarmes()):
                        if (ha, ma, sa) == alarme.get_time():
                            self.alarmes.remove_alarme(index)
                            break
            except ValueError as e:
                print(f"Alarme ValueError : {e}")
                return
            except Exception as e:
                print(f"Alarme exception {e}")
        else:
            self.loggin.log(
                f'{h:02d}:{m:02d}:{s:02d} : R : {topic.replace("home", "~")} : {msg}',
                color=color,
                aff=(Page.get_page() == 'mqttlogs'))
        self.nb_msg += 1
        if Page.get_page() == 'mqttlogs':
            stat = self.loggin.get_stat()
            self.display.set_pen(Color.BLACK)
            self.display.rectangle(360, 0, 479, 28)
            self.display.set_pen(Color.GREY)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 20)
            string = f"{stat:.1f} msg/mn"
            length = int(self.vector.measure_text(string)[2])
            self.vector.text(string, 479 - length, 22)
            self.presto.update()

    def affiche(self):
        self.display.set_pen(Color.BLACK)  # Black background
        self.display.clear()
        self.presto.update()
        self.loggin.new_message = True  # forcer le premier affichage
        while True:
            if self.alarmes.check_alarm():
                self.alerte.alerte("C'est l'heure !")
            verifier_connexion(self.presto, self.loggin)
            if get_touch(self.touch) == 'R':
                return
            try:
                # Wait for MQTT messages (non-blocking check)
                self.mqtt.check_msg()
            except Exception as e:
                print(f"Error while waiting for MQTT messages: {e}")
            if Page.get_page() != 'mqttlogs':
                return
            time.sleep(.1)
            self.display.set_pen(Color.BLACK)
            self.display.rectangle(0, 0, 120, 28)
            s = time.time()
            offset = 3600 * TZ.get_offset(s)
            _, _, _, h, m, s, _, _ = time.gmtime(s + offset)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 24)
            self.display.set_pen(Color.GREY)
            self.vector.text(f"{h:02d}:{m:02d}:{s:02d}", 0, 24)
            if self.loggin.new_message:
                self.loggin.update_screen()
            self.presto.update()
