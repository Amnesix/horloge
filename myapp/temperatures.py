import gc
import time

from requests import get

from myapp.secret import headers
from myapp.utils import CAPTEURS, TZ, Color, get_api

ASK_ALL_TEMP = True


class Temperatures:
    temps = {}

    def __init__(self, presto, display, vector, touch, loggin,
                 initiale_states):
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        self.api = get_api()
        self.t_cyan = display.create_pen(28, 132, 132)
        self.t_bleu = display.create_pen(28, 92, 132)
        self.t_vert = display.create_pen(28, 132, 32)
        self.t_jaune = display.create_pen(132, 132, 32)
        self.t_orange = display.create_pen(132, 92, 32)
        self.t_rouge = display.create_pen(132, 32, 32)
        self.t_violet = display.create_pen(132, 32, 132)
        for k, v in CAPTEURS.items():
            try:
                self.temps[k] = float(initiale_states["sensor." + v[1]])
            except KeyError:
                self.temps = {k: -1000. for k in CAPTEURS}
            except ValueError:
                self.temps[k] = -1000.
            except Exception as e:
                print(f"Exception non gérée {e}")
        # Tendances par défaut : idem températures actuelles
        self.tendance = {k: v for k, v in self.temps.items()}

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

    def get_all_temp(self):
        # Récupération de tous les états
        # Cette solution est peut-être plus lente. À vérifier.
        try:
            # t_start = time.ticks_ms()
            response = get(self.api + "states", headers=headers, timeout=5.0)
            all_states = response.json()
            # Extraction des températures
            temperatures = {
                s["entity_id"]: s["state"]
                for s in all_states if s["entity_id"] in
                ["sensor." + w[1] for w in CAPTEURS.values()]
            }
            # t_end = time.ticks_ms()
            # delai = t_end - t_start
            # print(f"get_all_temp() ok en {delai}ms")
            # Mise à jour de la table
            for key in self.temps:
                s = temperatures["sensor." + CAPTEURS[key][1]]
                self.temps[key] = float(s)
            try:
                response.close()
            except Exception as e:
                print(f"Erreur de fermeture réponse : {e} ({type(e)})")
        except Exception as e:
            print(f"Lecture températures erreur {e} ({type(e)})")

    def maj_temp(self):
        for k, v in self.temps.items():
            self.tendance[k] = v
        if ASK_ALL_TEMP:
            self.get_all_temp()
        else:
            for k in CAPTEURS:
                self.temps[k] = self.get_temp(k)

    def to_str(self, capteur):
        return f"{self.temps[capteur]:.1f}°C"

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
        first = True
        self.display.set_pen(Color.BLACK)
        self.display.clear()
        self.presto.update()
        fg = Color.GREY
        while True:
            # t_start = time.ticks_ms()
            self.touch.poll()
            if self.touch.state and self.touch.y > 64:
                self.display.set_pen(Color.BLACK)
                self.display.clear()
                return
            s = time.time()
            offset = 3600 * TZ.get_offset(s)
            if last_time == s:
                time.sleep(0.1)
                continue
            _, _, _, hour, minute, second, _, _ = time.gmtime(s + offset)
            if (minute % 15) == 0 and second == 0 or first:
                first = False
                for k, v in self.temps.items():
                    self.tendance[k] = v
                self.maj_temp()
                self.display.set_pen(Color.BLACK)
                self.display.clear()
                self.display.set_pen(fg)
                self.vector.set_font("Roboto-Medium-With-Material-Symbols.af",
                                     48)
                self.vector.text("Températures", (480 - w) // 2, 50)
                self.vector.set_font("Roboto-Medium-With-Material-Symbols.af",
                                     32)
                h = 1
                for name in sorted(self.temps.keys()):
                    temp = self.temps[name]
                    ok = self.get_temp_color(temp)
                    self.vector.text(CAPTEURS[name][0], 10, h * 40 + 80)
                    if ok:
                        self.vector.text(f"{temp:.1f}°C", 256, h * 40 + 80)
                        if temp < self.tendance[name]:
                            s = f"-{self.tendance[name] - temp:.1f}°C"
                        elif temp > self.tendance[name]:
                            s = f"+{temp - self.tendance[name]:.1f}°C"
                        else:
                            s = "="
                        self.vector.text(s, 380, h * 40 + 80)
                    else:
                        self.vector.text("indisponible", 256, h * 40 + 80)
                    h += 1
                self.presto.update()

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
