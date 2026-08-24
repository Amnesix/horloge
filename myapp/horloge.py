import datetime
import gc
import sys
import time

from picovector import Polygon
from touch import Button

from myapp.utils import (
    CAPTEURS,
    JOURS,
    PRISES,
    RETRAITE,
    TZ,
    Color,
    Page,
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
    sup = 0

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
        loggin,
        tests,
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
        self.loggin = loggin
        self.local = True
        self.tests = tests
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
        self.titre = f"{__title__} - Version {__version__}"
        len = int(self.vector.measure_text(self.titre)[2])
        self.loggin.log(self.titre, (WIDTH - len) // 2)
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 25)
        self.fg = Color.GREY

        self.next_update_time = time.time() + 12 * 60 * 60

        self.hub = Polygon()
        self.hub.circle(int(WIDTH / 2), int(HEIGHT / 2), 7)

        self.contour = Polygon()
        self.contour.circle(int(WIDTH / 2), int(HEIGHT / 2), int(HEIGHT / 2))
        self.fg_contour = Color.CYAN
        self.face = Polygon()
        self.face.circle(int(WIDTH / 2), int(HEIGHT / 2), int(HEIGHT / 2) - 3)

        self.tick_mark = Polygon()
        self.tick_mark.rectangle(int(WIDTH / 2) - 3, 10, 6, int(HEIGHT / 48))

        self.hour_mark = Polygon()
        self.hour_mark.rectangle(int(WIDTH / 2) - 5, 10, 10, int(HEIGHT / 10))

        self.minute_hand_length = int(HEIGHT / 2) - int(HEIGHT / 8)
        self.minute_hand = Polygon()
        self.minute_hand.path(
            (-5, -self.minute_hand_length),
            (-10, int(HEIGHT / 16)),
            (10, int(HEIGHT / 16)),
            (5, -self.minute_hand_length),
            (0, -self.minute_hand_length - 5),
        )

        self.hour_hand_length = int(HEIGHT / 2) - int(HEIGHT / 4.5)
        self.hour_hand = Polygon()
        self.hour_hand.path(
            (-5, -self.hour_hand_length),
            (-10, int(HEIGHT / 16)),
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
        self.date_box.rectangle(WIDTH // 2 - 75, 128, 150, 35)
        self.btn_date = Button(WIDTH // 2 - 75, 128, 150, 35)
        self.retraite_box = Polygon()
        self.retraite_box.rectangle(WIDTH // 2 - 50, 320, 100, 35)
        self.e_temp_box = Polygon()
        self.e_temp_box.rectangle(WIDTH // 4 - 45, HEIGHT // 2 - 18, 90, 36)
        self.b_temp_box = Polygon()
        self.b_temp_box.rectangle(WIDTH // 4 * 3 - 45, HEIGHT // 2 - 18, 90,
                                  36)
        self.btn_test = Button(*self.e_temp_box.bounds())

        self.switch_btn = Polygon()
        self.switch_btn.circle(32, 40, 20, stroke=2)
        self.temps_btn = Polygon()
        self.temps_btn.circle(447, 40, 20, stroke=2)
        self.sw = {k: Polygon() for k in PRISES.keys()}
        x, y = 5, 5
        for k in self.sw.keys():
            self.sw[k].circle(x, y, 4)
            x += 10
        self.key_sw = list(self.sw.keys())
        self.id_sw = 0
        self.tmp = {k: Polygon() for k in CAPTEURS.keys()}
        x, y = 400, 5
        for k in self.temperatures.temps.keys():
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
        self.display.set_pen(self.fg_contour)
        self.vector.draw(self.contour)
        # self.calendar.affiche()

    def gere_touch(self):

        def wait_for_release():
            while self.touch.state:
                self.touch.poll()

        ret = False
        self.touch.poll()
        if self.touch.state:
            # On attend le relaché...
            x, y = self.touch.x, self.touch.y
            if 0 <= x < 64 and 0 <= y < 64:
                wait_for_release()
                Page.set_page('switches')
                ret = True
            elif 416 <= x < 480 and 0 <= y < 64:
                wait_for_release()
                Page.set_page('temperatures')
                ret = True
            elif 200 <= x <= 280 and 200 <= y <= 280:
                wait_for_release()
                Page.set_page('flip')
                ret = True
            elif self.btn_date.is_pressed():
                wait_for_release()
                Page.set_page('calendrier')
                ret = True
            elif self.btn_test.is_pressed():
                wait_for_release()
                Page.set_page('tests')
                ret = True
        return ret

    def affiche(self):
        while True:
            verifier_connexion(self.presto, self.loggin)
            self.mqtt.check_msg()
            if Page.page != 'horloge':
                return
            if self.gere_touch():
                continue
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
            # if (minute % 15) == 0 and second == 0:
            #     self.temperatures.maj_temp()

            self.tr.reset()
            self.display.set_pen(Color.BLACK)
            self.display.clear()
            self.display.set_pen(Color.CYAN)
            self.vector.draw(self.contour)
            if ((hour == 11 and minute == 59) or
                (hour == 17 and minute == 14)) and second in (40, 42, 44):
                self.display.set_pen(Color.RED)
            else:
                self.display.set_pen(Color.LIGHTYELLOW)
            self.vector.draw(self.face)
            # self.display.circle(int(WIDTH / 2), int(HEIGHT / 2), int(HEIGHT / 2) - 4)

            x, y = (WIDTH // 2, HEIGHT // 2)
            angle_minute = minute * 6
            angle_minute += second / 10.0
            angle_hour = (hour % 12) * 30
            angle_hour += minute / 2
            angle_second = second * 6
            self.display.set_pen(Color.BLACK)
            # Dessin des repères des minutes
            for a in range(60):
                self.tr.rotate(360 / 60.0 * a, (x, y))
                self.vector.draw(self.tick_mark)
                self.tr.reset()
            # Dessin des repères des heures
            for a in range(12):
                self.tr.rotate(360 / 12.0 * a, (x, y))
                self.vector.draw(self.hour_mark)
                self.tr.reset()

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
            self.display.set_pen(Color.BLACK)
            self.vector.draw(self.date_box)
            self.vector.draw(self.retraite_box)
            self.vector.text(JOURS[wd], self.pos_jours[wd], 122)
            self.vector.text(self.retraite[0], self.retraite[1],
                             self.retraite[2])
            self.display.set_pen(Color.CYAN)
            self.vector.draw(self.switch_btn)
            self.vector.draw(self.temps_btn)
            self.display.set_pen(Color.GREY)
            self.vector.text(f"{day:02d}/{month:02d}/{year}", WIDTH // 2 - 68,
                             155)
            diff = (RETRAITE - datetime.date(year, month, day)).days
            self.vector.text(f"J-{diff:04d}", WIDTH // 2 - 42, 347)
            # Affichage des dates et retraite au dessus des aiguilles heures & minutes
            dehors = self.temperatures.temps["_dehors"]
            bureau = self.temperatures.temps["bureau"]
            if dehors > -1000 and bureau > -1000:
                self.display.set_pen(Color.BLACK)
                self.vector.draw(self.b_temp_box)
                self.vector.draw(self.e_temp_box)
                self.vector.text(self.dehors[0], self.dehors[1],
                                 self.dehors[2])
                self.vector.text(self.bureau[0], self.bureau[1],
                                 self.bureau[2])
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
            self.display.set_pen(Color.GREY)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 42)
            self.vector.text("S", 22, 53)
            self.vector.text("T", 437, 55)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 16)
            self.vector.text(__title__ + " - " + __version__, 380, 475)
            self.vector.text(__python__, 10, 475)
            self.vector.text(f"Overrun {self.sup * 100 // self.total:d}%", 400,
                             460)
            # Aiguille des secondes au dessus de l'ensemble
            self.display.set_pen(Color.RED)
            self.tr.rotate(angle_second, (WIDTH // 2, HEIGHT // 2))
            self.tr.translate(x, y)
            self.vector.draw(self.second_hand)
            self.tr.reset()
            self.vector.draw(self.hub)

            # À priori, demander l'ensemble des états et filtrer est beaucoup
            # plus long que demander les états séparéments.
            # if self.local or second in (1, 16, 31, 46):
            #     self.switches.get_all_states()
            ok = True
            for key in self.key_sw:
                if ok:
                    state = self.switches.get_state(key, False)
                else:
                    state = None
                if state is None:
                    self.display.set_pen(Color.GREY)
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
                self.sup += 1
                self.local = False
            elif not self.local and second == 1:
                self.local = True
            self.total += 1
            self.display.set_pen(Color.GREY)
            self.vector.text(f"{delai}ms", 10, 460)

            self.presto.update()
