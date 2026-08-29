import time

import presto
from picovector import ANTIALIAS_BEST, PicoVector, Transform

from myapp.alarmes import Alarm
from myapp.calendar import Calendar
from myapp.flip_clock import Flip_Clock
from myapp.horloge import Horloge
from myapp.mqtt import MQTT, MQTTLog
from myapp.switches import Switches
from myapp.temperatures import Temperatures
from myapp.utils import (
    TZ,
    Alerte,
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
alerte = Alerte(presto, display, vector, touch, loggin)
alarmes = Alarm(presto, display, vector, touch, alerte, loggin)
# Initialistion des objets
broker, port = get_api()[1]
mqtt = MQTT(broker, port, loggin)
mqttlogs = MQTTLog(presto, display, vector, touch, mqtt, alerte, alarmes)
calendar = Calendar(presto, display, vector, touch, mqtt, loggin)
initiale_states = get_all_states()
# Création des différents objets
temperatures = Temperatures(presto, display, vector, touch, mqtt, loggin,
                            initiale_states)
switches = Switches(presto, display, vector, touch, mqtt, loggin,
                    initiale_states)
flip = Flip_Clock(presto, display, vector, touch, mqtt, loggin)
horloge = Horloge(presto, display, vector, t, touch, flip, mqtt, temperatures,
                  switches, calendar, alarmes, loggin, mqttlogs)

# Lancement de l'affichage principal
loggin.log("Lancement boucle de traitement")
while True:
    page = Page.get_page()
    if page == 'horloge':
        horloge.affiche()
    elif page == 'calendrier':
        calendar.affiche()
    elif page == 'flip':
        flip.affiche()
    elif page == 'switches':
        switches.affiche()
    elif page == 'temperatures':
        temperatures.affiche()
    elif page == 'mqttlogs':
        mqttlogs.affiche()
    elif page == 'exit':
        break

print("The end")
display.set_pen(Color.BLACK)
display.clear()
presto.update()
mqtt.disconnect()
# presto.wifi.disconnect()
