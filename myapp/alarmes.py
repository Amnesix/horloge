import time

from myapp.utils import TZ


class Alarm:
    alarmes = [(11, 59, 40), (16, 44, 40), (17, 14, 40)]

    def __init__(self, presto, display, vector, touch, alerte, loggin):
        loggin.log("Initialisation Alames")
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        self.alerte = alerte

    def add_alarme(self, hour, minute, seconde):
        if (hour, minute, seconde) in self.alarmes:
            return
        self.alarmes.append((hour, minute, seconde))
        self.alarmes.sort()

    def next_alarme(self):
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
        self.alarmes.pop(self.alarmes.index((hour, minute, seconde)))
