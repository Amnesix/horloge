import gc
import sys
import time

import jpegdec
from picovector import Polygon

from myapp.utils import (
    JOURS,
    MOIS,
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
        calendar,
        alarmes,
        alerte,
        loggin,
    ):
        self.presto = presto
        self.display = display
        self.vector = vector
        self.tr = tr
        self.touch = touch
        self.flip = flip
        self.mqtt = mqtt
        self.calendar = calendar
        self.alarmes = alarmes
        self.alerte = alerte
        self.loggin = loggin
        self.local = True
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
        self.fg = Color.LIGHTGREY
        self.titre = f"{__title__} - {__version__}"
        self.pos_jours = []
        self.mqtt.set_callback(self.cb_msg)
        self.topic = None
        self.t_msg = 0
        self.m_msg = ""
        self.offset = 0
        self.first_lave_linge = True
        # len = int(self.vector.measure_text(self.titre)[2])
        self.loggin.log(f"Initialisation {self.titre}")
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 25)
        # Pour le décodage de l'image de fond
        self.jpg = jpegdec.JPEG(self.display)

        self.next_update_time = time.time() + 12 * 60 * 60

        self.hub = Polygon()
        self.hub.circle(int(WIDTH / 4), int(HEIGHT / 4), 5)

        self.minute_hand_length = int(HEIGHT / 4) - int(HEIGHT / 16)
        self.minute_hand = Polygon()
        self.minute_hand.path(
            (-3, -self.minute_hand_length),
            (-4, int(HEIGHT / 32)),
            (0, int(HEIGHT / 32) - 1),
            (4, int(HEIGHT / 32)),
            (3, -self.minute_hand_length),
            (0, -self.minute_hand_length - 3),
        )

        self.hour_hand_length = int(HEIGHT / 4) - int(HEIGHT / 9)
        self.hour_hand = Polygon()
        self.hour_hand.path(
            (-4, -self.hour_hand_length),
            (-5, int(HEIGHT / 32)),
            (0, int(HEIGHT / 32) - 1),
            (5, int(HEIGHT / 32)),
            (3, -self.hour_hand_length),
            (0, -self.hour_hand_length - 3),
        )

        self.second_hand_length = int(HEIGHT / 4) - int(HEIGHT / 16)
        self.second_hand = Polygon()
        self.second_hand.path(
            (-1, -self.second_hand_length),
            (-1, int(HEIGHT / 16)),
            (1, int(HEIGHT / 16)),
            (1, -self.second_hand_length),
        )

        self.display.set_pen(Color.BLACK)
        self.display.clear()

    def cb_msg(self, topic, _):
        self.topic = topic.replace('home', '~')
        self.t_msg = time.time()
        _, _, _, h, m, s, _, _ = time.gmtime(self.t_msg + self.offset)
        self.m_msg = f"mqttlm {h:02d}:{m:02d}:{s:02d}"

    def gere_touch(self):

        def wait_for_release():
            while self.touch.state:
                self.touch.poll()

        data = get_touch(self.touch)
        if data is None:
            return False
        if data == 'L':
            Page.clear()
            return True
        return False

    def affiche(self):
        self.first = True
        while True:
            if verifier_connexion(self.presto, self.loggin):
                self.mqtt.reconnect()
            self.mqtt.check_msg()
            if self.gere_touch() or Page.get_page() != 'horloge':
                return
            now = time.time()
            if now == self.next_update_time:
                update_time(self.loggin, False)
            self.offset = 3600 * TZ.get_offset(now)
            year, month, day, hour, minute, second, wd, _ =\
                time.gmtime(now + self.offset)
            if self.last_second == second:
                time.sleep_ms(10)
                continue
            if self.first:
                self.calendar.affiche()
                self.first = False
            self.last_second = second
            if self.alerte.id_show:
                self.alerte.show()
            self.tr.reset()
            self.display.set_pen(Color.BLACK)
            self.display.clear()
            self.jpg.open_file("img/cadran_240.jpg")
            self.jpg.decode(0, 0, jpegdec.JPEG_SCALE_HALF, dither=True)

            x, y = (WIDTH // 4, HEIGHT // 4)
            angle_minute = minute * 6
            angle_minute += second / 10.0
            angle_hour = (hour % 12) * 30
            angle_hour += minute / 2
            angle_second = second * 6

            self.display.set_pen(Color.DARKJAUNE)

            # Dessin des aiguilles
            self.tr.rotate(angle_minute, (x, y))
            self.tr.translate(x, y)
            self.vector.draw(self.minute_hand)
            self.tr.reset()

            self.tr.rotate(angle_hour, (x, y))
            self.tr.translate(x, y)
            self.vector.draw(self.hour_hand)
            self.tr.reset()

            self.display.set_pen(Color.RED)
            self.tr.rotate(angle_second, (x, y))
            self.tr.translate(x, y)
            self.vector.draw(self.second_hand)
            self.tr.reset()
            self.vector.draw(self.hub)

            self.display.set_pen(Color.GREY)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 40)
            jour = f"{JOURS[wd]}"
            dim = self.vector.measure_text(jour)
            self.vector.text(jour, 360 - int(dim[2] // 2), 40)
            date = f"{day}"
            dim = self.vector.measure_text(date)
            self.vector.text(date, 360 - int(dim[2] // 2), 80)
            mois = f"{MOIS[month]}"
            dim = self.vector.measure_text(mois)
            self.vector.text(mois, 360 - int(dim[2] // 2), 120)
            annee = f"{year}"
            dim = self.vector.measure_text(annee)
            self.vector.text(annee, 360 - int(dim[2] // 2), 160)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 64)
            heure = f"{hour}:{minute:02d}"
            dim = self.vector.measure_text(heure)
            self.vector.text(heure, 360 - int(dim[2] // 2), 230)

            gc.collect()
            self.total += 1

            self.presto.partial_update(0, 0, 480, 240)
