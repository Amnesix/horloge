import datetime
import math
import time

import ntptime
from picovector import Polygon
from requests import get, post

from myapp.secret import APIHA, CONFIG, MQTT_DISTANT, headers

RETRAITE = datetime.date(2029, 7, 1)

NTPHOST = (
    "0.fr.pool.ntp.org",
    "1.fr.pool.ntp.org",
    "2.fr.pool.ntp.org",
    "3.fr.pool.ntp.org",
    "pool.ntp.org",
)

JOURS = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi",
         "Dimanche")
MOIS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)

CAPTEURS = {
    "_dehors": ("Extérieur", "th_dehors_temperature", "th_dehors_humidity"),
    "bureau": ("Bureau", "th_bureau_temperature", "th_bureau_humidity"),
    "cyril": ("Chambre Cyril", "th_cyril_temperature", "th_cyril_humidity"),
    "buandrie": ("Arrière cuisine", "th_arriere_cuisine_temperature",
                 "th_arriere_cuisine_humidity"),
    "cuisine": ("Cuisine", "th_cuisine_temperature", "th_cuisine_humidity"),
    "douche": ("Douche", "th_douche_temperature", "th_douche_humidity"),
    "parents":
    ("Chambre parents", "th_parent_temperature", "th_parent_humidity"),
    "salon": ("Salon", "th_salon_temperature", "th_salon_humidity"),
}

# Dictionnaires de PRISES connectées
# Les libellés sont ceux affichés et sont succeptibles de changer.
PRISES = {
    "Ventilo": "antela_prise_intelligente_2_socket_1",
    "RPi": "pipmc_net_194_socket_1",
    "Multimédia": "multimedia_salon_socket_1",
    "Cuisine": "prise_connectee",
    "Buandrie": "lave_linge",
    "Douche": "sonoff_s60zbtpf",
}

SENSOR_to_CAPTEURS = {
    "sensor.th_dehors_temperature": "_dehors",
    "sensor.th_bureau_temperature": "bureau",
    "sensor.th_cyril_temperature": "cyril",
    "sensor.th_arriere_cuisine_temperature": "buandrie",
    "sensor.th_cuisine_temperature": "cuisine",
    "sensor.th_douche_temperature": "douche",
    "sensor.th_parent_temperature": "parents",
    "sensor.th_salon_temperature": "salon",
}

HUMIDITY_to_CAPTEURS = {
    "sensor.th_dehors_humidity": "_dehors",
    "sensor.th_bureau_humidity": "bureau",
    "sensor.th_cyril_humidity": "cyril",
    "sensor.th_arriere_cuisine_humidity": "buandrie",
    "sensor.th_cuisine_humidity": "cuisine",
    "sensor.th_douche_humidity": "douche",
    "sensor.th_parent_humidity": "parents",
    "sensor.th_salon_humidity": "salon",
}

PAGES = ('calendrier', 'flip', 'switches', 'temperatures', 'mqttlogs',
         'horloge')
COMMANDES = PAGES + ('next', 'prev', 'exit')

# Dictionnaires de PRISES connectées
# Les libellés sont ceux affichés et sont succeptibles de changer.
SWITCH_to_PRISES = {
    "switch.antela_prise_intelligente_2_socket_1": "Ventilo",
    "switch.pipmc_net_194_socket_1": "RPi",
    "switch.multimedia_salon_socket_1": "Multimédia",
    "switch.prise_connectee": "Cuisine",
    "switch.sapin_socket_1": "Buandrie",
    "switch.sonoff_s60zbtpf": "Douche"
}

template_temperatures = """
[
{% for s in states.sensor
   if s.attributes.device_class == 'temperature' %}
  {
    "entity_id": {{ s.entity_id | tojson }},
    "state": {{ s.state | tojson }},
    "attributes": {{ s.attributes | tojson }}
  }{% if not loop.last %},{% endif %}
{% endfor %}
]
"""
template_humidities = """
[
{% for s in states.sensor
   if s.attributes.device_class == 'humidity' %}
  {
    "entity_id": {{ s.entity_id | tojson }},
    "state": {{ s.state | tojson }},
    "attributes": {{ s.attributes | tojson }}
  }{% if not loop.last %},{% endif %}
{% endfor %}
]
"""
template_switch = """
[
{% for s in states.switch %}
  {
    "entity_id": {{ s.entity_id | tojson }},
    "state": {{ s.state | tojson }},
    "attributes": {{ s.attributes | tojson }}
  }{% if not loop.last %},{% endif %}
{% endfor %}
]
"""

FILTRES = []
NB_MAX_HISTO = 100
NB_MAX_DISPLAY = 18

net_config = 0
api = APIHA
mqtt = MQTT_DISTANT


def set_api(indice):
    global api, mqtt
    api = CONFIG[indice][2]
    mqtt = CONFIG[indice][3]


def get_api():
    return (api, mqtt)


class Log:

    def __init__(self, presto, display, vector, title):
        self.presto = presto
        self.display = display
        self.vector = vector
        self.title = title
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
        len = self.vector.measure_text(self.title)
        self.title_coord = (int(480 - len[2]) // 2, 25)
        self.ligne = 0
        self.msg = []
        self.new_message = True

    def set_title(self, title):
        self.title = title

    def log(self, msg, color=None, nl=True, aff=True):
        if color is None:
            color = Color.GREY
        if nl:
            self.msg.append((time.time(), msg, color))
            if len(self.msg) > NB_MAX_HISTO:
                self.msg.pop(0)
        else:
            # Remplace le dernier message
            self.msg[-1] = (time.time(), msg, color)
        self.new_message = True
        if aff:
            self.update_screen()

    def update_screen(self):
        self.display.set_pen(Color.BLACK)
        self.display.clear()
        self.display.set_pen(Color.GREY)
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
        self.vector.text(self.title, *self.title_coord)
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 25)
        for index, data in enumerate(self.msg[-NB_MAX_DISPLAY::]):
            try:
                self.display.set_pen(data[2])
            except IndexError:
                print(data)
            self.vector.text(data[1], 0, (index + 2) * 25)
        self.presto.update()
        self.new_message = False

    def get_stat(self):
        """Nombre de message par minutes sur les len(msg) derniers messages"""
        if len(self.msg) > 0:
            delai = (time.time() - self.msg[0][0]) / 60.
            if delai > 0.:
                return len(self.msg) / delai
        return 0


def wifi_connect(presto, loggin=None):
    global net_config

    def teste_connexion():
        # Pourquoi ça tombe régulièrement en timeout ?
        if not presto.wifi.isconnected():
            if loggin:
                loggin.log("Non connecté !")
            return False
        try:
            response = get(api, headers=headers, timeout=5.0)
            if loggin:
                loggin.log(response.text)
            return True
        except Exception as e:
            if loggin:
                loggin.log(f"wifi_connect():Exception ({e})")
            print(f"wifi_connect():Exception ({e})")
        return False

    indice = net_config
    while True:
        if loggin is not None:
            loggin.log(f" * SSID={CONFIG[indice][0]} : ")
        ok = presto.connect(ssid=CONFIG[indice][0], password=CONFIG[indice][1])
        if ok:
            if loggin is not None:
                loggin.log(f" * SSID={CONFIG[indice][0]} : OK", nl=False)
            net_config = indice
            set_api(indice)
            if loggin is not None:
                loggin.log(f"IP : {presto.wifi.ipv4()}")
            teste_connexion()
            return
        if loggin is not None:
            loggin.log(f" * SSID={CONFIG[indice][0]} : NOK", nl=False)
        indice = (indice + 1) % len(CONFIG)


def verifier_connexion(presto, loggin):
    """En cas de perte de connexion, tentative de reconnexion"""
    if not presto.wifi.isconnected():
        loggin.log("Perte de connexion !")
        loggin.log("Nouvelle tentative de connexion...")
        wifi_connect(presto, loggin)
        return True
    return False


def get_all_states_old():
    global FILTRES
    FILTRES = ["sensor." + v[1] for v in CAPTEURS.values()]
    FILTRES += ["switch." + v for v in PRISES.values()]
    states = {}
    try:
        # t_start = time.ticks_ms()
        response = get(api + "states", headers=headers, timeout=5.0)
        lst = response.json()
        states = {
            s["entity_id"]:
            '-1000.' if s["state"] == 'unavailable' else s["state"]
            for s in lst if s["entity_id"] in FILTRES
        }
        try:
            response.close()
        except Exception as e:
            print(f"Erreur de fermeture réponse : {e} ({type(e)})")
    except Exception as e:
        print(f"Lecture states erreur {e} ({type(e)})")
    return states


def get_states(template):
    states = {}
    try:
        response = post(api + "template",
                        headers=headers,
                        json={"template": template})
        if response.status_code == 200:
            states = response.json()
        else:
            print(f"status_code = {response.status_code}")
        try:
            response.close()
        except Exception:
            pass
    except Exception as e:
        print(f"Exception template : {e}")
    return states


def get_temperatures():
    """Récupération des températures"""
    result = {}
    states = get_states(template_temperatures)
    for state in states:
        temp = state['state']
        result[state[
            'entity_id']] = "Non valide" if temp == "unavailable" else float(
                temp)
    return result


def get_humidities():
    """Récupération des températures"""
    result = {}
    states = get_states(template_humidities)
    for state in states:
        temp = state['state']
        result[state[
            'entity_id']] = "Non valide" if temp == "unavailable" else float(
                temp)
    return result


def get_switches():
    """Récupération de l'état des switches"""
    result = {}
    states = get_states(template_switch)
    for state in states:
        entity = state['entity_id']
        if entity.split('.')[1] in PRISES.values():
            result[entity] = state['state'] == 'on'
    return result


def get_all_states():
    """Récupération initiale des switches et des températures"""
    states = get_temperatures()
    states |= get_humidities()
    states |= get_switches()
    return states


class Test_Recup:

    def __init__(self, presto, display, vector, touch, loggin):
        self.presto = presto
        self.display = display
        self.vector = vector
        self.loggin = Log(presto, display, vector, "TEST RECUP.")
        self.touch = touch

    def affiche(self):
        states = {}
        while True:
            self.touch.poll()
            if self.touch.state:
                while True:
                    self.touch.poll()
                    if not self.touch.state:
                        break
                if self.touch.y > 380:
                    return
                start = time.ticks_ms()
                if self.touch.x < 240:
                    states = get_temperatures()
                else:
                    states = get_switches()
                delai = time.ticks_ms() - start
                self.loggin.log(f"Récupération en {delai}ms")
                for k, v in states.items():
                    self.loggin.log(f"{k}: {v}")
            self.presto.update()
            time.sleep(.1)


def get_touch(touch) -> tuple[int, int] | str | None:
    touch.poll()
    if touch.state:
        xs, ys = touch.x, touch.y
        while touch.state:
            touch.poll()
        dx, dy = xs - touch.x, ys - touch.y
        if math.sqrt(dx * dx + dy * dy) > 100:
            if abs(dx) < abs(dy):
                if dy < 0:
                    return 'D'
                else:
                    return 'U'
            else:
                if dx < 0:
                    return 'L'
                else:
                    return 'R'
        else:
            return (xs, ys)
    return None


def get_page(touch) -> tuple[int, int] | bool:
    data = get_touch(touch)
    if data is None:
        return False
    if isinstance(data, (int, int)):
        return data
    if data == 'R':
        Page.set_page('next')
    elif data == 'L':
        Page.set_page('prev')
    return True


def update_time(loggin, show_log=True):
    # Mise à l'heure
    if show_log:
        loggin.log("Mise à l'heure")
    server = 0
    while True:
        s = f" * Serveur NTP {NTPHOST[server]}"
        if show_log:
            loggin.log(s)
        ntptime.timeout = 5
        ntptime.host = NTPHOST[server]
        try:
            ntptime.settime()
        except Exception:
            if show_log:
                s += " : Erreur !"
                loggin.log(s, nl=False)
            server = (server + 1) % 4
        else:
            if show_log:
                s += " : OK"
                loggin.log(s, nl=False)
            return


class Page:
    """Gestion des pages"""
    __page = 'horloge'

    @classmethod
    def set_page(cls, page):
        if page not in COMMANDES:
            return
        if page == 'next':
            cls.__page = PAGES[(PAGES.index(cls.__page) + 1) % len(PAGES)]
        elif page == 'prev':
            cls.__page = PAGES[(PAGES.index(cls.__page) + len(PAGES) - 1) %
                               len(PAGES)]
        else:
            cls.__page = page

    @classmethod
    def get_page(cls):
        return cls.__page

    @classmethod
    def clear(cls):
        cls.__page = ''


class TZ:
    """Classe minimaliste permettant de connaitre le
    décalage horraire sur le fuseau de Paris en
    tenant compte de l'heure d'été."""
    _ready = False
    start = None
    end = None

    @classmethod
    def init(cls, loggin, year=None):
        if cls._ready:
            return
        if year is None:
            s = time.time()
            year, _, _, _, _, _, _, _ = time.gmtime(s)
        cls.start = cls.dst_start(year)
        cls.end = cls.dst_end(year)
        _, ms, js, _, _, _, _, _ = time.gmtime(cls.start)
        _, me, je, _, _, _, _, _ = time.gmtime(cls.end)
        loggin.log(
            f"{year} : heure été du {js} {MOIS[ms - 1]} au {je} {MOIS[me - 1]}"
        )
        _ready = True

    @classmethod
    def get_offset(cls, s):
        return 2 if cls.start <= s <= cls.end else 1

    @classmethod
    def dst_start(cls, year):
        last_sun_march = 31
        # Rechercher le dernier dimanche du mois de mars
        for day in range(31, 24, -1):
            if (time.localtime(time.mktime(
                (year, 3, day, 2, 0, 0, 0, 0, 0)))[6] == 6):  # dimanche
                last_sun_march = day
                break
        return time.mktime((year, 3, last_sun_march, 2, 0, 0, 0, 0, 0))

    @classmethod
    def dst_end(cls, year):
        last_sun_oct = 31
        # Rechercher le dernier dimanche du mois d'octobre
        for day in range(31, 24, -1):
            if time.localtime(time.mktime(
                (year, 10, day, 3, 0, 0, 0, 0, 0)))[6] == 6:
                last_sun_oct = day
                break
        return time.mktime((year, 10, last_sun_oct, 3, 0, 0, 0, 0, 0))


class Color:
    _ready = False
    BLACK = None
    WHITE = None
    GREY = None
    RED = None
    GREEN = None
    BLUE = None
    LIGHTRED = None
    LIGHTGREEN = None
    LIGHTBLUE = None
    ORANGE = None
    CYAN = None
    LIGHTYELLOW = None
    LIGHTGREY = None
    DARKGREY = None

    @classmethod
    def init(cls, display):
        if cls._ready:
            return
        cls.BLACK = display.create_pen(0, 0, 0)
        cls.WHITE = display.create_pen(255, 255, 255)
        cls.GREY = display.create_pen(127, 127, 127)
        cls.RED = display.create_pen(127, 0, 0)
        cls.GREEN = display.create_pen(0, 127, 0)
        cls.BLUE = display.create_pen(0, 0, 127)
        cls.LIGHTRED = display.create_pen(255, 0, 0)
        cls.LIGHTGREEN = display.create_pen(0, 255, 0)
        cls.LIGHTBLUE = display.create_pen(0, 0, 255)
        cls.ORANGE = display.create_pen(127, 39, 5)
        cls.CYAN = display.create_pen(0, 127, 127)
        cls.LIGHTYELLOW = display.create_pen(126, 130, 94)
        cls.LIGHTGREY = display.create_pen(96, 96, 96)
        cls.DARKGREY = display.create_pen(64, 64, 64)
        cls._ready = True


class Alerte:
    message = []

    def __init__(self, presto, display, vector, touch, loggin):
        loggin.log("Initialisation alertes")
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        self.loggin = loggin
        self.cadre = Polygon()
        self.cadre.rectangle(98, 78, 284, 154)
        self.fond = Polygon()
        self.fond.rectangle(100, 80, 280, 150)

    def alerte(self, msg):
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
        words = msg.split()
        self.message.clear()
        self.message.append(words.pop(0))
        while len(words):
            word = words.pop(0)
            w = self.vector.measure_text(f"{self.message[-1]} {word}")[2]
            if w > 260:
                self.message.append(word)
            else:
                self.message[-1] += " " + word
        self.show()

    def show(self, timeout=10):
        # Fin de l'affichage :
        s = time.time() + timeout
        self.display.set_pen(Color.CYAN)
        self.vector.draw(self.cadre)
        self.display.set_pen(Color.RED)
        self.vector.draw(self.fond)
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
        self.display.set_pen(Color.LIGHTYELLOW)
        hp = 170 - len(self.message) * 15
        for pos, line in enumerate(self.message):
            dim = self.vector.measure_text(line, x=0, y=0, angle=0)
            offset = 130 - int(dim[2]) // 2
            self.vector.text(line, 110 + offset, hp + pos * 32)
        self.presto.update()
        while time.time() < s:
            time.sleep(.25)
