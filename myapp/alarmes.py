import json
import time

from myapp.utils import JOURS, TZ


class Alarme:

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
        str += f" - oneshot {('non', 'oui')[self.oneshot]}"
        return str


class Alarmes:
    alarmes = [
        Alarme(11, 59, 40, -1, False),
        Alarme(16, 44, 40, -1, False),
        Alarme(17, 14, 40, 4, False)
    ]

    def __init__(self, presto, display, vector, touch, alerte, loggin):
        loggin.log("Initialisation Alames")
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        self.alerte = alerte
        self.load_alarmes()
        # Création de la page

    def add_alarme(self, hour, minute, seconde, jour=-1, oneshot=True):
        al = Alarme(hour, minute, seconde, jour, oneshot)
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
            if 0 < da != d:
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

    def affiche(self):
        pass
