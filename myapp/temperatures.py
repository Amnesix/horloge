import gc
import time

from requests import get

from myapp.secret import headers
from myapp.utils import CAPTEURS, TZ, Color, get_api, get_temperatures

ASK_ALL_TEMP = True
ASK_VIA_TEMPLATE = True
# Demande température toutes les X mn
DEMANDE = 5


class Temperatures:
    temps = {}
    humidity = {}
    maj = {}

    def __init__(self, presto, display, vector, touch, mqtt, loggin,
                 initiale_states):
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        self.mqtt = mqtt
        self.api = get_api()[0]
        self.t_cyan = display.create_pen(28, 132, 132)
        self.t_bleu = display.create_pen(28, 92, 132)
        self.t_vert = display.create_pen(28, 132, 32)
        self.t_jaune = display.create_pen(132, 132, 32)
        self.t_orange = display.create_pen(132, 92, 32)
        self.t_rouge = display.create_pen(132, 32, 32)
        self.t_violet = display.create_pen(132, 32, 132)
        s = time.time()
        for k, v in CAPTEURS.items():
            self.maj[k] = s
            try:
                self.temps[k] = float(initiale_states["sensor." + v[1]])
            except KeyError:
                self.temps = {k: -1000. for k in CAPTEURS}
            except ValueError:
                self.temps[k] = -1000.
            except Exception as e:
                print(f"Exception non gérée {e}")
            try:
                self.humidity[k] = float(initiale_states["sensor." + v[2]])
            except KeyError:
                self.humidity = {k: 0 for k in CAPTEURS}
            except ValueError:
                self.humidity[k] = 0
            except Exception as e:
                print(f"Exception non gérée {e}")
        # Tendances par défaut : idem températures actuelles
        s = time.time()
        self.tendance = {k: [v, s] for k, v in self.temps.items()}
        self.mqtt.set_callback(self.update_temp)
        self.mqtt.set_callback(self.update_humidity)

    def get_temp(self, capteur: str) -> float:
        try:
            url = self.api + "states/sensor." + CAPTEURS[capteur][1]
            response = get(url, headers=headers, timeout=2.0)
            result = response.json()
            ret = float(result["state"])
            try:
                response.close()
            except Exception:
                pass
        except Exception:
            ret = -1000.
        return ret

    def update_temp(self, topic, value):
        """Mise à jour de la température via MQTT"""
        if "temp" not in topic:
            return
        room = self.mqtt.get_room(topic)
        self.maj[room] = time.time()
        try:
            if room in self.temps:
                self.tendance[room] = [self.temps[room], time.time()]
                self.temps[room] = float(value)
        except ValueError:
            self.temps[room] = -1000.

    def update_humidity(self, topic, value):
        """Mise à jour de la température via MQTT"""
        if "humidity" not in topic:
            return
        room = self.mqtt.get_room(topic)
        self.maj[room] = time.time()
        try:
            if room in self.humidity:
                self.humidity[room] = float(value)
        except ValueError:
            self.humidity[room] = 0

    def get_all_temp(self):
        # Récupération de tous les états
        # Cette solution est peut-être plus lente. À vérifier.
        response = None
        try:
            if ASK_VIA_TEMPLATE:
                temperatures = get_temperatures()
            else:
                response = get(self.api + "states",
                               headers=headers,
                               timeout=5.0)
                all_states = response.json()
                # Extraction des températures
                temperatures = {
                    s["entity_id"]: s["state"]
                    for s in all_states if s["entity_id"] in
                    ["sensor." + w[1] for w in CAPTEURS.values()]
                }
            # Mise à jour de la table
            for key in self.temps:
                try:
                    s = temperatures["sensor." + CAPTEURS[key][1]]
                    self.temps[key] = float(s)
                except ValueError:
                    self.temps[key] = -1000.
            if not ASK_VIA_TEMPLATE:
                try:
                    if response:
                        response.close()
                except Exception as e:
                    print(f"Erreur de fermeture réponse : {e} ({type(e)})")
        except Exception as e:
            print(f"Lecture températures erreur {e} ({type(e)})")

    def maj_temp(self):
        s = time.time()
        for k, v in self.temps.items():
            self.tendance[k] = [v, s]
        if ASK_ALL_TEMP:
            self.get_all_temp()
        else:
            for k in CAPTEURS:
                self.temps[k] = self.get_temp(k)

    """def to_str(self, capteur):
        return f"{self.temps[capteur]:.1f}°C" """

    def get_temp_color(self, temp):
        ret = True
        if temp == -1000:
            self.display.set_pen(Color.DARKGREY)
            ret = False
        elif temp < 6:
            self.display.set_pen(self.t_cyan)
        elif 6 <= temp < 19:
            self.display.set_pen(self.t_bleu)
        elif 19 <= temp < 24:
            self.display.set_pen(self.t_vert)
        elif 24 <= temp < 28:
            self.display.set_pen(self.t_jaune)
        elif 28 <= temp < 32:
            self.display.set_pen(self.t_orange)
        elif 32 <= temp < 36:
            self.display.set_pen(self.t_rouge)
        else:
            self.display.set_pen(self.t_violet)
        return ret

    def affiche(self):
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 48)
        w = int(self.vector.measure_text("Température")[2])
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 28)
        lh = list(map(int, self.vector.measure_text("##:##:##")))
        last_time = 0
        self.display.set_pen(Color.BLACK)
        self.display.clear()
        self.presto.update()
        fg = Color.GREY
        # self.maj_temp()
        while True:
            # t_start = time.ticks_ms()
            self.touch.poll()
            if self.touch.state and self.touch.y > 64:
                self.display.set_pen(Color.BLACK)
                self.display.clear()
                return
            s = time.time()
            offset = 3600 * TZ.get_offset(s)
            self.mqtt.check_msg()
            if last_time == s:
                time.sleep(0.1)
                continue
            last_time = s
            _, _, _, hour, minute, second, _, _ = time.gmtime(s + offset)
            self.display.set_pen(Color.BLACK)
            self.display.clear()
            self.display.set_pen(fg)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 48)
            self.vector.text("Températures", (480 - w) // 2, 50)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
            h = 3
            for name in sorted(self.temps.keys()):
                temp = self.temps[name]
                ok = self.get_temp_color(temp)
                if s - self.maj[name] < 10:
                    self.display.circle(10, h * 40 - 10, 6)
                self.vector.text(CAPTEURS[name][0], 30, h * 40)
                if ok:
                    self.vector.text(f"{temp:.1f}°C", 270, h * 40)
                    if s - self.tendance[name][1] > 120:
                        self.tendance[name][0] = temp
                    if temp < self.tendance[name][0]:
                        # d = f"-{self.tendance[name][0] - temp:.1f}°C"
                        self.display.line(360, h * 40 - 10, 370, h * 40 - 10)
                        self.display.line(370, h * 40 - 10, 380, h * 40)
                    elif temp > self.tendance[name][0]:
                        # d = f"+{temp - self.tendance[name][0]:.1f}°C"
                        self.display.line(360, h * 40 - 10, 370, h * 40 - 10)
                        self.display.line(370, h * 40 - 10, 380, h * 40 - 20)
                    else:
                        # d = "="
                        self.display.line(360, h * 40 - 10, 380, h * 40 - 10)
                    # self.vector.text(d, 380, h * 40)
                    hu = self.humidity[name]
                    self.vector.text(f"{hu:.0f}%", 400, h * 40)
                else:
                    self.vector.text("indisponible", 256, h * 40)
                h += 1

            self.display.set_pen(fg)
            self.display.line(0, 70, 479, 70)
            self.display.line(0, 440, 479, 440)

            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 28)
            time.sleep(0.1)
            self.display.set_pen(Color.BLACK)
            self.display.rectangle((479 - lh[2]) // 2 - 2, 468 - lh[3],
                                   lh[2] + 4, lh[3] + 4)
            heure = f"{hour:02d}:{minute:02d}:{second:02d}"
            self.display.set_pen(fg)
            self.vector.text(heure, (480 - lh[2]) // 2, 470)
            self.presto.update()
            gc.collect()
            # t_end = time.ticks_ms()
            # print(f"Boucle : {t_end - t_start}ms")
