import time

import presto
from picovector import ANTIALIAS_BEST, PicoVector, Transform

from myapp.calendar import Calendar
from myapp.flip_clock import Flip_Clock
from myapp.horloge import Horloge
from myapp.mqtt import MQTT, MQTTLog
from myapp.switches import Switches
from myapp.temperatures import Temperatures
from myapp.utils import (
    TZ,
    Color,
    Log,
    Page,
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
broker, port = get_api()[1]
mqtt = MQTT(broker, port, loggin)
calendar = Calendar(presto, display, vector, touch, mqtt, loggin)
initiale_states = get_all_states()
tests = MQTTLog(presto, display, vector, touch, mqtt, loggin)
# Création des différents objets
temperatures = Temperatures(presto, display, vector, touch, mqtt, loggin,
                            initiale_states)
switches = Switches(presto, display, vector, touch, mqtt, loggin,
                    initiale_states)
flip = Flip_Clock(presto, display, vector, touch, mqtt)
horloge = Horloge(presto, display, vector, t, touch, flip, mqtt, temperatures,
                  switches, calendar, loggin, tests)

# Lancement de l'affichage principal
while True:
    print(f"> {Page.page}")
    if Page.page == 'horloge':
        horloge.affiche()
    elif Page.page == 'calendrier':
        calendar.affiche()
    elif Page.page == 'flip':
        flip.affiche()
    elif Page.page == 'switches':
        switches.affiche()
    elif Page.page == 'temperatures':
        temperatures.affiche()
    elif Page.page == 'tests':
        tests.affiche()
    elif Page.page == 'exit':
        break

print("The end")
display.set_pen(Color.BLACK)
display.clear()
presto.update()
mqtt.disconnect()
# presto.wifi.disconnect()
