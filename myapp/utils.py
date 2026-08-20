import datetime
import time

import ntptime
from requests import get, post

from myapp.secret import APIHA, CONFIG, headers

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
    "_dehors": ("Extérieur", "th_dehors_temperature"),
    "bureau": ("Bureau", "th_bureau_temperature"),
    "cyril": ("Chambre Cyril", "ewelink_th01_temperature"),
    "buandrie": ("Arrière cuisine", "th_arriere_cuisine_temperature"),
    "cuisine": ("Cuisine", "th_cuisine_temperature"),
    "diane": ("Chambre Diane", "th_diane_temperature"),
    "parents": ("Chambre parents", "th_parent_temperature"),
    "salon": ("Salon", "th_salon_temperature"),
}

# Dictionnaires de PRISES connectées
# Les libellés sont ceux affichés et sont succeptibles de changer.
PRISES = {
    "Ventilo": "antela_prise_intelligente_2_socket_1",
    "RPi": "pipmc_net_194_socket_1",
    "Multimédia": "multimedia_salon_socket_1",
    "Cuisine": "prise_connectee",
    "Buandrie": "sapin_socket_1",
    "Douche": "sonoff_s60zbtpf",
}

SENSOR_to_CAPTEURS = {
    "sensor.th_dehors_temperature": "_dehors",
    "sensor.th_bureau_temperature": "bureau",
    "sensor.ewelink_th01_temperature": "cyril",
    "sensor.th_arriere_cuisine_temperature": "buandrie",
    "sensor.th_cuisine_temperature": "cuisine",
    "sensor.th_diane_temperature": "diane",
    "sensor.th_parent_temperature": "parents",
    "sensor.th_salon_temperature": "salon",
}

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

net_config = 0
api = APIHA


def set_api(indice):
    global api
    api = CONFIG[indice][2]


def get_api():
    return api


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

    def set_title(self, title):
        self.title = title

    def log(self, msg, nl=True):
        if nl:
            self.msg.append(msg)
            if len(self.msg) >= 19:
                self.msg.pop(0)
        else:
            self.msg[-1] = msg
        self.display.set_pen(Color.BLACK)
        self.display.clear()
        self.display.set_pen(Color.GREY)
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
        self.vector.text(self.title, *self.title_coord)
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 25)
        for line in range(len(self.msg)):
            self.vector.text(self.msg[line], 0, (line + 2) * 25)
        self.presto.update()


def wifi_connect(presto, loggin=None):
    global net_config

    def test_connexion():
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
                loggin.log(f"Exception ({e})")
            print(f"Exception ({e})")
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
            """print(
                f"Configuration :\n\t- Connexion sur {CONFIG[indice][0]}\n\t- API : {api}"
            )"""
            if loggin is not None:
                loggin.log(f"IP : {presto.wifi.ipv4()}")
            if not test_connexion():
                # En cas d'erreur, on retente une fois
                test_connexion()
            return CONFIG[indice][3]
        if loggin is not None:
            loggin.log(f" * SSID={CONFIG[indice][0]} : NOK", nl=False)
        indice = (indice + 1) % len(CONFIG)


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
    result = {}
    states = get_states(template_temperatures)
    for state in states:
        temp = state['state']
        result[state[
            'entity_id']] = "Non valide" if temp == "unavailable" else float(
                temp)
    return result


def get_switches():
    result = {}
    states = get_states(template_switch)
    for state in states:
        entity = state['entity_id']
        if entity.split('.')[1] in PRISES.values():
            result[entity] = state['state'] == 'on'
    return result


def get_all_states():
    states = get_temperatures()
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


class TZ:
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
        for day in range(31, 24, -1):
            if (time.localtime(time.mktime(
                (year, 3, day, 2, 0, 0, 0, 0, 0)))[6] == 6):  # dimanche
                last_sun_march = day
                break
        return time.mktime((year, 3, last_sun_march, 2, 0, 0, 0, 0, 0))

    @classmethod
    def dst_end(cls, year):
        last_sun_oct = 31
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
