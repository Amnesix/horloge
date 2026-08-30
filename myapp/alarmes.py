import json
import time

from myapp.utils import TZ


class Alarm:
    alarmes = [[11, 59, 40], [16, 44, 40], [17, 14, 40]]

    def __init__(self, presto, display, vector, touch, alerte, loggin):
        loggin.log("Initialisation Alames")
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        self.alerte = alerte
        self.load_alarmes()

    def add_alarme(self, hour, minute, seconde):
        if [hour, minute, seconde] in self.alarmes:
            return
        self.alarmes.append([hour, minute, seconde])
        print(self.alarmes)
        self.alarmes.sort()
        self.save_alarmes()

    def next_alarme(self) -> tuple(int, int, int):
        t = time.time()
        t += TZ.get_offset(t) * 3600
        _, _, _, h, m, s, _, _ = time.gmtime(t)
        for index, value in enumerate(self.alarmes):
            ha, ma, sa = value
            if (ha, ma, sa) < (h, m, s):
                continue
            return (ha, ma, sa)
        return self.alarmes[0]

    def remove_alarme(self, hour, minute, seconde):
        self.alarmes.pop(self.alarmes.index([hour, minute, seconde]))
        self.save_alarmes()

    def get_alarmes(self) -> list(tuple[int, int, int]):
        return self.alarmes

    def check_alarm(self) -> bool:
        t = time.time()
        t += TZ.get_offset(t) * 3600
        _, _, _, h, m, s, _, _ = time.gmtime(t)
        for index, value in enumerate(self.alarmes):
            if (h, m, s) == value:
                return True
        return False

    def save_alarmes(self):
        with open("alarmes.json", "wt") as f:
            json.dump(self.alarmes, f)

    def load_alarmes(self):
        try:
            with open("alarmes.json", "rt") as f:
                data = json.load(f)
            print(data)
        except Exception as e:
            print(f"load_alarmes() : {e}")
            self.save_alarmes()
        else:
            self.alarmes = data
