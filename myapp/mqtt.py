import binascii
import gc
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
    "home/switch/rpi": "RPi",
    "home/switch/eth": "Ethernet",
    "home/switch/multimedia": "Multimédia",
    "home/switch/cuisine": "Cuisine",
    "home/switch/douche": "Douche",
    "home/switch/lave_linge": "Buandrie",
    # Lave lave_linge
    "home/lave_linge/puissance": "Machine",
    "home/lave_linge/fincycle": "-",
    # Autres
    "home/page": "-",
    "home/commandes": "-",
    "home/alerte": "-",
    "home/alarme": "-",
    "home/debug": "print('OK, je suis là')",
    "home/pong": ""
}

TOPIC_MSG = {
    "RPi": "home/toggle/rpi",
    "Douche": "home/toggle/douche",
    "Cuisine": "home/toggle/cuisine",
    "Ventilo": "home/toggle/ventilo",
    "Buandrie": "home/toggle/lave_linge",
    "Multimédia": "home/toggle/multimedia",
    "Ethernet": "home/toggle/eth",
    "ping": "home/ping",
}


class MQTT:
    lv = None
    puissance = "0.0"
    last_ping = 0

    def __init__(self, broker, port, alerte, loggin):
        loggin.log("Initialisation MQTT")
        self.broker = broker
        self.port = port
        self.alerte = alerte
        self.loggin = loggin
        self.callbacks = []
        self.pile = []
        self.fin_init = False
        self.last_msg = 0
        unique = str(binascii.hexlify(machine.unique_id()))
        self.client_id = f'{unique}'
        self.connect()
        loggin.log(f"Connecté à MQTT à {broker}:{port}.")

    def set_fin_init(self):
        self.fin_init = True

    def connect(self):
        self.client = MQTTClient(self.client_id,
                                 self.broker,
                                 port=self.port,
                                 keepalive=600)
        self.client.set_callback(self.mqtt_callback)
        self.set_callback(self.mqtt_commandes)
        try:
            self.client.connect()
            self.loggin.log("Client MQTT connecté")
            t = len(SOUSCRIPTIONS)
            for n, k in enumerate(SOUSCRIPTIONS):
                # ATTENTION : Le loggin ralenti l'intialisation du presto…
                s = f"Souscription : {(n + 1) * 100 / t:.0f}%"
                self.loggin.log(s, nl=False)
                self.client.subscribe(k)
        except OSError as e:
            print(f"Erreur de connexion : {e}")
            self.loggin.log(f"Erreur MQTT : {e}")

    def disconnect(self):
        if self.client is not None:
            # Ce module MQTTClient n'a pas de méthode unsubscribe !
            # for n, k in enumerate(SOUSCRIPTIONS):
            #     self.client.unsubscribe(k)
            self.client.disconnect()
        self.client = None

    def reconnect(self):
        self.loggin.log("Déconnexion client MQTT")
        if self.client is not None:
            self.client.disconnect()
        self.loggin.log("Connexion client MQTT")
        self.connect()

    def send_msg(self, what, msg):
        # print(f"Send {what}: {TOPIC_MSG[what]}:'{msg}'")
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
        self.last_msg = time.time()
        _, _, _, h, m, s, _, _ = time.gmtime(self.last_msg + 3600 *
                                             TZ.get_offset(self.last_msg))
        if 'pong' in topic:
            print(f"{h:02d}:{m:02d}:{s:02d}:Réception MQTT {topic} : {msg}")
            if len(self.pile) == 0:
                return
        else:
            print(
                f"{h:02d}:{m:02d}:{s:02d}:Réception MQTT {topic} : {msg} --> Empilé"
            )
            self.pile.append((topic, msg))
        if not self.fin_init:
            return
        while len(self.pile):
            topic, msg = self.pile.pop(0)
            for fct in self.callbacks:
                try:
                    fct(topic, msg)
                except Exception as e:
                    print(f"Erreur mqtt_callback() : {e} ({topic}, {msg})")
                    print(fct.__name__)

    def mqtt_commandes(self, topic, msg):
        if 'page' in topic:
            Page.set_page(msg)

    def get_room(self, topic):
        return SOUSCRIPTIONS[topic]

    def check_msg(self):
        if time.time() - self.last_ping >= 60:
            self.send_msg("ping", "")
            self.last_ping = time.time()
        try:
            if self.client is not None:
                self.client.check_msg()
        except OSError:
            print("Deconnexion MQTT")
            self.connect()
        except Exception as e:
            print(f"Error while waiting for MQTT messages: {e}")
        if self.lv and time.time() - self.lv > 60 and self.puissance == "0.0":
            self.lv = None


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
        elif 'puissance' in topic:
            color = Color.LIGHTYELLOW
            self.mqtt.lv = time.time()
            self.mqtt.puissance = msg
        elif 'fincycle' in topic:
            self.alerte.alerte("Machine terminée")
        else:
            color = Color.LIGHTGREY
        if 'alert' in topic:
            self.alerte.alerte(msg)
        elif 'debug' in topic:
            print(exec(msg))
        elif 'alarme' in topic:
            # print(f'Alarme : {msg}')
            try:
                if msg.lower() in ('list', 'liste'):
                    aff = Page.get_page() == 'mqttlogs'
                    for index, al in enumerate(self.alarmes.get_alarmes()):
                        try:
                            s = f"Alarme #{index} : {al}"
                            # print(s)
                            self.loggin.log(s, aff=aff)
                        except ValueError:
                            print(f"List alarmes ValueError : {al}")
                    return
                if 'del' in msg and '#' in msg:
                    indice = int(msg.split('#')[1])
                    self.alarmes.remove_alarme(indice)
                    return
                cmd, ha, ma, sa, *suite = msg.split()
                jour, oneshot = '-1', True
                if len(suite):
                    jour = suite.pop(0)
                if len(suite):
                    oneshot = suite.pop(0) in ('1', 'true', 'True')
                ha, ma, sa, jour = map(int, (ha, ma, sa, jour))
                if cmd == 'add':
                    self.loggin.log(
                        f"{h:02d}:{m:02d}:{s:02d} : A : ADD Alarm at {ha:d}:{ma:02d}:{sa:02d}",
                        aff=Page.get_page() == 'mqttlogs',
                        color=Color.ORANGE)
                    self.alarmes.add_alarme(ha, ma, sa, jour, oneshot)
                elif cmd == 'del':
                    self.loggin.log(
                        f"{h:02d}:{m:02d}:{s:02d} : A : DEL Alarm at {ha:2d}:{ma:02d}:{sa:02d}",
                        aff=Page.get_page() == 'mqttlogs',
                        color=Color.ORANGE)
                    for index, alarme in enumerate(self.alarmes.get_alarmes()):
                        if (ha, ma, sa) == alarme.get_time():
                            if jour == -1 or jour == alarme.get_day():
                                self.alarmes.remove_alarme(index)
                            break
            except ValueError as e:
                print(f"Alarme ValueError : {e}")
                return
            except Exception as e:
                print(f"Alarme exception {e}")
        else:
            le = topic.split('/')[1][0].upper()
            self.loggin.log(
                f'{h:02d}:{m:02d}:{s:02d} : {le} : {topic.replace("home", "~")} : {msg}',
                color=color,
                aff=(Page.get_page() == 'mqttlogs'))
        self.nb_msg += 1
        if Page.get_page() == 'mqttlogs':
            stat = self.loggin.get_stat()
            self.display.set_pen(Color.BLACK)
            self.display.rectangle(360, 0, 479, 28)
            self.display.set_pen(Color.LIGHTGREY)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 20)
            string = f"{stat:.1f} msg/mn"
            length = int(self.vector.measure_text(string)[2])
            self.vector.text(string, 479 - length, 22)
            self.presto.update()

    def affiche(self):
        self.display.set_pen(Color.BLACK)  # Black background
        self.display.clear()
        self.presto.update()
        # forcer le premier affichage
        self.loggin.new_message = True
        while True:
            if self.alarmes.check_alarm():
                self.alerte.alerte("C'est l'heure !")
            verifier_connexion(self.presto, self.loggin)
            if get_touch(self.touch) == 'R' or Page.get_page() != 'mqttlogs':
                if Page.get_page() == 'mqttlogs':
                    Page.clear()
                return
            try:
                # Wait for MQTT messages (non-blocking check)
                self.mqtt.check_msg()
            except Exception as e:
                print(f"Error while waiting for MQTT messages: {e}")
            if self.loggin.new_message or Page.get_redraw():
                self.loggin.update_screen()
                Page.set_redraw(False)
            time.sleep(.1)
            t = time.time()
            offset = 3600 * TZ.get_offset(t)
            _, _, _, h, m, s, _, _ = time.gmtime(t + offset)
            self.display.set_pen(Color.BLACK)
            self.display.rectangle(0, 0, 120, 28)
            self.display.set_pen(Color.LIGHTGREY)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 24)
            self.vector.text(f"{h:02d}:{m:02d}:{s:02d}", 0, 24)
            self.presto.update()
            gc.collect()
            time.sleep(.1)
