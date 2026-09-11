import datetime
import gc
import sys
import time

import jpegdec
from picovector import Polygon

from myapp.utils import (
    CAPTEURS,
    JOURS,
    PRISES,
    RETRAITE,
    TZ,
    Color,
    Page,
    get_touch,
    update_time,
    verifier_connexion,
)
from myapp.version import __title__, __version__

v = sys.version
__python__ = "µPython - " + v.split(";")[0]

WIDTH, HEIGHT = 480, 480


class Horloge:
    pos_jours = []
    last_second = 0
    total = 1

    def __init__(
        self,
        presto,
        display,
        vector,
        tr,
        touch,
        flip,
        mqtt,
        temperatures,
        switches,
        calendar,
        alarmes,
        alerte,
        loggin,
        mqttlogs,
    ):
        self.presto = presto
        self.display = display
        self.vector = vector
        self.tr = tr
        self.touch = touch
        self.flip = flip
        self.mqtt = mqtt
        self.temperatures = temperatures
        self.switches = switches
        self.calendar = calendar
        self.alarmes = alarmes
        self.alerte = alerte
        self.loggin = loggin
        self.local = True
        self.mqttlogs = mqttlogs
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
        self.fg = Color.LIGHTGREY
        self.titre = f"{__title__} - Version {__version__}"
        # len = int(self.vector.measure_text(self.titre)[2])
        self.loggin.log(f"Initialisation {self.titre}")
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 25)
        # Pour le décodage de l'image de fond
        self.jpg = jpegdec.JPEG(self.display)

        self.next_update_time = time.time() + 12 * 60 * 60

        self.hub = Polygon()
        self.hub.circle(int(WIDTH / 2), int(HEIGHT / 2), 7)

        self.minute_hand_length = int(HEIGHT / 2) - int(HEIGHT / 8)
        self.minute_hand = Polygon()
        self.minute_hand.path(
            (-5, -self.minute_hand_length),
            (-8, int(HEIGHT / 16)),
            (0, int(HEIGHT / 16) - 2),
            (8, int(HEIGHT / 16)),
            (5, -self.minute_hand_length),
            (0, -self.minute_hand_length - 5),
        )

        self.hour_hand_length = int(HEIGHT / 2) - int(HEIGHT / 4.5)
        self.hour_hand = Polygon()
        self.hour_hand.path(
            (-5, -self.hour_hand_length),
            (-10, int(HEIGHT / 16)),
            (0, int(HEIGHT / 16) - 2),
            (10, int(HEIGHT / 16)),
            (5, -self.hour_hand_length),
            (0, -self.hour_hand_length - 5),
        )

        self.second_hand_length = int(HEIGHT / 2) - int(HEIGHT / 8)
        self.second_hand = Polygon()
        self.second_hand.path(
            (-2, -self.second_hand_length),
            (-2, int(HEIGHT / 8)),
            (2, int(HEIGHT / 8)),
            (2, -self.second_hand_length),
        )

        self.date_box = Polygon()
        self.date_box.rectangle(WIDTH // 2 - 77, 128, 154, 35,
                                (18, 18, 18, 18))
        self.retraite_box = Polygon()
        self.retraite_box.rectangle(WIDTH // 2 - 52, 320, 104, 35,
                                    (18, 18, 18, 18))
        self.e_temp_box = Polygon()
        self.e_temp_box.rectangle(WIDTH // 4 - 47, HEIGHT // 2 - 18, 94, 36,
                                  (18, 18, 18, 18))
        self.b_temp_box = Polygon()
        self.b_temp_box.rectangle(WIDTH // 4 * 3 - 47, HEIGHT // 2 - 18, 94,
                                  36, (18, 18, 18, 18))
        self.sw = {k: Polygon() for k in PRISES}
        x, y = 5, 15
        for k in self.sw:
            self.sw[k].circle(x, y, 4)
            x += 10
        self.key_sw = list(self.sw.keys())
        self.id_sw = 0
        self.tmp = {k: Polygon() for k in CAPTEURS}
        x, y = 5, 5
        for k in self.temperatures.temps:
            self.tmp[k].circle(x, y, 4)
            x += 10
        self.key_tmp = list(self.tmp.keys())
        self.id_tmp = 0

        self.retraite = ["Retraite", WIDTH, 312]
        self.dehors = ["Dehors", WIDTH // 4, HEIGHT // 2 - 26]
        self.bureau = ["Bureau", WIDTH // 4 * 3, HEIGHT // 2 - 26]
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
        r = self.vector.measure_text(self.retraite[0])[2]
        self.retraite[1] = int((self.retraite[1] - r) / 2)
        d = self.vector.measure_text(self.dehors[0])[2]
        self.dehors[1] = int(self.dehors[1] - d / 2)
        b = self.vector.measure_text(self.bureau[0])[2]
        self.bureau[1] = int(self.bureau[1] - b / 2)
        for txt in JOURS:
            self.pos_jours.append(
                int((WIDTH - self.vector.measure_text(txt)[2]) / 2))
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 25)
        self.display.set_pen(Color.BLACK)
        self.display.clear()

    def gere_touch(self):

        def wait_for_release():
            while self.touch.state:
                self.touch.poll()

        data = get_touch(self.touch)
        if data is None:
            return False
        if data == 'R':
            Page.clear()
            return True
        return False

    def affiche(self):
        while True:
            if verifier_connexion(self.presto, self.loggin):
                self.mqtt.reconnect()
            self.mqtt.check_msg()
            if self.gere_touch() or Page.get_page() != 'horloge':
                return
            t_start = time.ticks_ms()
            s = time.time()
            if s == self.next_update_time:
                update_time(False)
            offset = 3600 * TZ.get_offset(s)
            year, month, day, hour, minute, second, wd, _ = time.gmtime(s +
                                                                        offset)
            if self.last_second == second:
                time.sleep_ms(10)
                continue
            self.last_second = second
            if self.alerte.id_show:
                self.alerte.show()
            self.tr.reset()
            self.display.set_pen(Color.BLACK)
            self.display.clear()
            index = self.alarmes.next_alarme()
            h, m, s = self.alarmes.get_alarme(index).get_time()
            # TODO: si s < 6 il faut tester m-1 !
            if hour == h and minute == m and second in ((s - 6) % 60,
                                                        (s - 4) % 60,
                                                        (s - 2) % 60, s):
                # self.display.set_pen(Color.RED)
                self.jpg.open_file("img/cadran_alarm.jpg")
                if second == s and self.alarmes.get_alarme(
                        index).get_oneshot():
                    self.alarmes.remove_alarme(index)
            else:
                # self.display.set_pen(Color.LIGHTYELLOW)
                self.jpg.open_file("img/cadran.jpg")
            self.jpg.decode(0, 0, jpegdec.JPEG_SCALE_FULL, dither=True)
            # self.vector.draw(self.face)

            x, y = (WIDTH // 2, HEIGHT // 2)
            angle_minute = minute * 6
            angle_minute += second / 10.0
            angle_hour = (hour % 12) * 30
            angle_hour += minute / 2
            angle_second = second * 6
            self.display.set_pen(Color.BLACK)

            self.display.set_pen(Color.DARKGREY)
            self.vector.draw(self.date_box)
            self.vector.draw(self.retraite_box)
            self.vector.draw(self.b_temp_box)
            self.vector.draw(self.e_temp_box)
            self.display.set_pen(Color.BLACK)

            # Dessin des aiguilles
            self.tr.rotate(angle_minute, (x, y))
            self.tr.translate(x, y)
            self.vector.draw(self.minute_hand)
            self.tr.reset()

            self.tr.rotate(angle_hour, (x, y))
            self.tr.translate(x, y)
            self.vector.draw(self.hour_hand)
            self.tr.reset()

            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
            self.vector.text(JOURS[wd], self.pos_jours[wd], 122)
            self.vector.text(self.retraite[0], self.retraite[1],
                             self.retraite[2])
            self.vector.text(self.dehors[0], self.dehors[1], self.dehors[2])
            self.vector.text(self.bureau[0], self.bureau[1], self.bureau[2])

            # Aiguille des secondes au dessus de l'ensemble
            self.display.set_pen(Color.RED)
            self.tr.rotate(angle_second, (WIDTH // 2, HEIGHT // 2))
            self.tr.translate(x, y)
            self.vector.draw(self.second_hand)
            self.tr.reset()
            self.vector.draw(self.hub)

            self.display.set_pen(Color.BLACK)
            self.display.set_pen(Color.LIGHTGREY)
            self.vector.text(f"{day:02d}/{month:02d}/{year}", WIDTH // 2 - 68,
                             155)
            diff = (RETRAITE - datetime.date(year, month, day)).days
            self.vector.text(f"J-{diff:04d}", WIDTH // 2 - 42, 347)

            # Affichage des dates et retraite au dessus des aiguilles heures & minutes
            self.display.set_pen(Color.BLACK)
            dehors = self.temperatures.temps["_dehors"]
            bureau = self.temperatures.temps["bureau"]
            self.temperatures.get_temp_color(dehors)
            self.vector.text(
                f"{dehors:.1f}°C" if dehors > -1000 else "  ???",
                WIDTH // 4 - 38,
                HEIGHT // 2 + 10,
            )
            self.temperatures.get_temp_color(bureau)
            self.vector.text(
                f"{bureau:.1f}°C" if bureau > -1000 else "  ???",
                WIDTH // 4 * 3 - 38,
                HEIGHT // 2 + 10,
            )
            self.display.set_pen(Color.LIGHTGREY)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 16)
            self.vector.text(__title__ + " - " + __version__, 380, 475)
            self.vector.text(__python__, 10, 475)
            if self.mqtt.puissance != "0.0":
                p = f"Lave linge {self.mqtt.puissance}W"
                self.vector.text(p, 479 - int(self.vector.measure_text(p)[2]),
                                 10)
            ok = True
            for key in self.key_sw:
                if ok:
                    state = self.switches.get_state(key, False)
                else:
                    state = None
                if state is None:
                    self.display.set_pen(Color.LIGHTGREY)
                    ok = False
                elif state:
                    self.display.set_pen(Color.GREEN)
                else:
                    self.display.set_pen(Color.RED)
                self.vector.draw(self.sw[key])
                self.id_sw = (self.id_sw + 1) % len(self.key_sw)
            for key in self.key_tmp:
                self.temperatures.get_temp_color(self.temperatures.temps[key])
                self.vector.draw(self.tmp[key])

            gc.collect()
            t_end = time.ticks_ms()
            delai = t_end - t_start
            if delai > 1500:
                # print(f"Boucle : {delai}ms")
                self.local = False
            elif not self.local and second == 1:
                self.local = True
            self.total += 1
            self.display.set_pen(Color.LIGHTGREY)
            self.vector.text(f"{delai}ms", 10, 460)

            self.presto.update()
