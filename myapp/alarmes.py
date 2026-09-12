import gc
import json
import time

import jpegdec

from myapp.utils import JOURS, TZ, Color

LARGEUR = 168
HAUTEUR = 80
ABVJ = ['lu', 'ma', 'me', 'je', 've', 'sa', 'di']


class MyBtn:
    """Classe de définition  de boutons perso"""

    def __init__(self, x, y, w, h, name, oneshot):
        self.name = name
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        self.w = w
        self.h = h
        self.oneshot = oneshot

    def clicked(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2


BTN = {
    "btn_p": (10, 75, 94, 47, True),
    "btn_n": (375, 75, 94, 47, True),
    "btn_next": (93, 135, 122, 48, True),
    "btn_del": (262, 135, 122, 48, True),
    "btn_new": (180, 197, 121, 48, True),
    "btn_hm": (36, 418, 52, 52, False),
    "btn_hp": (101, 418, 52, 52, False),
    "btn_mm": (182, 418, 52, 52, False),
    "btn_mp": (247, 418, 52, 52, False),
    "btn_sm": (328, 418, 52, 52, False),
    "btn_sp": (392, 418, 52, 52, False),
    "btn_lu": (24, 343, 32, 32, True),
    "btn_ma": (74, 343, 32, 32, True),
    "btn_me": (124, 343, 32, 32, True),
    "btn_je": (174, 343, 32, 32, True),
    "btn_ve": (224, 343, 32, 32, True),
    "btn_sa": (274, 343, 32, 32, True),
    "btn_di": (327, 343, 32, 32, True),
    "btn_oneshot": (408, 343, 32, 32, True),
}


class Alarme:
    """
    Définition d'une alame. Paramètres :
    heure, minute[, seconde]
    """

    def __init__(self, heure, minute, seconde=0, jour=-1, oneshot=True):
        self.heure = heure
        self.minute = minute
        self.seconde = seconde
        self.jour = jour
        self.oneshot = oneshot

    def get_time(self):
        return self.heure, self.minute, self.seconde

    def get_day(self):
        return self.jour

    def get_oneshot(self):
        return self.oneshot

    def dump(self) -> tuple[int, int, int, int, bool]:
        return (self.heure, self.minute, self.seconde, self.jour, self.oneshot)

    def _t(self):
        return self.jour * 86400 + self.heure * 3600 + self.minute * 60 + self.seconde

    def __lt__(self, other):
        return self._t() < other._t()

    def __gt__(self, other):
        return self._t() > other._t()

    def __le__(self, other):
        return self._t() <= other._t()

    def __ge__(self, other):
        return self._t() >= other._t()

    def __eq__(self, other):
        return self._t() == other._t()

    def __str__(self):
        str = f"{self.heure:02d}:{self.minute:02d}:{self.seconde:02d}"
        str += f" - j:{'*' if self.jour == -1 else JOURS[self.jour]}"
        str += f" - {('', 'oneshot')[self.oneshot]}"
        return str


class Alarmes:
    new_al = None

    def __init__(self, presto, display, vector, touch, alerte, loggin):
        loggin.log("Initialisation Alarmes")
        self.btn = {}
        self.alarmes = []
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        self.alerte = alerte
        self.load_alarmes()
        self.jpg = jpegdec.JPEG(self.display)
        for k, v in BTN.items():
            x, y, w, h, oneshot = v
            self.btn[k] = MyBtn(x, y, w, h, k, oneshot)

    def add_alarme(self, heure, minute, seconde, jour=-1, oneshot=True):
        if seconde == 0:
            seconde = 59
            minute = (minute + 59) % 60
            if minute == 59:
                heure = (heure + 23) % 24
                if (heure, minute, seconde) == (23, 59, 59) and jour != -1:
                    jour = (jour + 6) % 7
        al = Alarme(heure, minute, seconde, jour, oneshot)
        if al in self.alarmes:
            return
        self.alarmes.append(al)
        print(al)
        self.alarmes.sort()
        self.save_alarmes()

    def next_alarme(self) -> int:
        t = time.time()
        t += TZ.get_offset(t) * 3600
        _, _, _, h, m, s, d, _ = time.gmtime(t)
        for index, value in enumerate(self.alarmes):
            ha, ma, sa = value.get_time()
            da = value.get_day()
            if (ha, ma, sa) < (h, m, s):
                continue
            if 0 <= da != d:
                continue
            return index
        # Donc, la prochaine alarme est la première et ça sera pour demain
        return 0

    def remove_alarme(self, index):
        self.alarmes.pop(index)
        self.save_alarmes()

    def get_alarme(self, index):
        return self.alarmes[index]

    def get_alarmes(self) -> list[Alarme]:
        return self.alarmes

    def check_alarm(self) -> bool:
        t = time.time()
        t += TZ.get_offset(t) * 3600
        _, _, _, h, m, s, _, _ = time.gmtime(t)
        for index, value in enumerate(self.alarmes):
            if (h, m, s) == value.get_time():
                return True
        return False

    def save_alarmes(self):
        data = []
        for al in self.alarmes:
            data.append((al.get_time(), al.get_day(), al.get_oneshot()))
        with open("alarmes.json", "wt") as f:
            json.dump(data, f)

    def load_alarmes(self):
        try:
            with open("alarmes.json", "rt") as f:
                data = json.load(f)
        except Exception as e:
            print(f"load_alarmes() : {e}")
            self.save_alarmes()
        else:
            self.alarmes.clear()
            for al in data:
                t, d, o = al
                h, m, s = t
                self.alarmes.append(Alarme(h, m, s, d, o))

    def btn_clicked(self, name):
        if name in map(lambda x: 'btn_' + x, ABVJ + ['oneshot']):
            print(f"btn {name} clické")
        elif name == 'btn_new':
            t = time.time()
            _, _, _, h, m, s, d, _ = time.gmtime(t + TZ.get_offset(t) * 3600)
            self.new_al = Alarme(h, m, s)
        elif name == 'btn_p':
            return len(self.alarmes) - 1
        elif name == 'btn_n':
            return 1
        elif self.new_al is not None:
            if name == 'btn_hm':
                self.new_al.heure = (self.new_al.heure + 23) % 24
            elif name == 'btn_hp':
                self.new_al.heure = (self.new_al.heure + 1) % 24
            elif name == 'btn_mm':
                self.new_al.minute = (self.new_al.minute + 59) % 60
            elif name == 'btn_mp':
                self.new_al.minute = (self.new_al.minute + 1) % 60
            elif name == 'btn_sm':
                self.new_al.seconde = (self.new_al.seconde + 59) % 60
            elif name == 'btn_sp':
                self.new_al.seconde = (self.new_al.seconde + 1) % 60
        return 0

    def affiche(self):
        """Affichage d'une interface de gestion"""
        index = self.next_alarme()
        while True:
            al = self.get_alarme(index)
            self.jpg.open_file("img/alarme.jpg")
            self.jpg.decode(0, 0, jpegdec.JPEG_SCALE_FULL, dither=True)
            self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
            s = f"{al.heure:02d}:{al.minute:02d}:{al.seconde:02d} "
            s += f"{'*' if al.jour == -1 else ABVJ[al.jour]} "
            s += f"{'oneshot' if al.oneshot else ''}"
            self.display.set_pen(Color.LIGHTYELLOW)
            pos = 240 - int(self.vector.measure_text(s)[2] / 2)
            self.vector.text(s, pos, 110)
            if self.new_al is not None:
                al = self.new_al
                pos = 240 - int(self.vector.measure_text(s)[2] / 2)
                s = f"{al.heure:02d}:{al.minute:02d}:{al.seconde:02d} "
                self.vector.text(s, pos, 280)
            self.presto.update()
            gc.collect()
            self.touch.poll()
            if self.touch.state:
                x, y = self.touch.x, self.touch.y
                if y < 48:
                    return
                for btn in self.btn.values():
                    if btn.clicked(x, y):
                        if btn.oneshot:
                            while self.touch.state:
                                self.touch.poll()
                        index = (index + self.btn_clicked(btn.name)) % len(
                            self.alarmes)
