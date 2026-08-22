import time

import presto
from picovector import ANTIALIAS_BEST, PicoVector, Transform

from myapp.calendar import Calendar
from myapp.flip_clock import Flip_Clock
from myapp.horloge import Horloge
from myapp.mqtt import MQTT
from myapp.switches import Switches
from myapp.temperatures import Temperatures
from myapp.utils import (
    TZ,
    Color,
    Log,
    Test_Recup,
    get_all_states,
    get_api,
    update_time,
    wifi_connect,
)
from myapp.version import __title__, __version__

# Initialisation générale
presto = presto.Presto(full_res=True)
display = presto.display
display.set_pen(display.create_pen(0, 0, 0))
display.clear()
presto.update()
touch = presto.touch
vector = PicoVector(display)
t = Transform()
vector.set_transform(t)
vector.set_antialiasing(ANTIALIAS_BEST)
Color.init(display)
loggin = Log(presto, display, vector, f"{__title__} - {__version__}")
loggin.log("Lancement application")
loggin.log("Connexion Wifi en cours...")

# bg = Color.BLACK
# fg = Color.WHITE

# Connection / Mise à l'heure
wifi_connect(presto, loggin)
update_time(loggin)
TZ.init(loggin)
s = time.time()
offset = 3600 * TZ.get_offset(s)
y, m, d, H, M, S, _, _ = time.gmtime(s + offset)
loggin.log(f"{y}/{m:02d}/{d:02d} {H:02d}:{M:02d}:{S:02d}")

# Initialistion des objets
calendar = Calendar(presto, display, vector, touch)
states = get_all_states()
# print(states)
# Tests accessibles depuis le 'bouton' température extérieur
tests = Test_Recup(presto, display, vector, touch, loggin)
broker, port = get_api()[1]
mqtt = MQTT(broker, port, loggin)
# Création des différents objets
temperatures = Temperatures(presto, display, vector, touch, mqtt, loggin,
                            states)
switches = Switches(presto, display, vector, touch, mqtt, states)
flip = Flip_Clock(presto, display, vector, touch)
horloge = Horloge(presto, display, vector, t, touch, flip, mqtt, temperatures,
                  switches, calendar, loggin, tests)

# Lancement de l'affichage principal
horloge.affiche()
