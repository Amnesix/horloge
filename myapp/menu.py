import gc
import time

from picovector import Polygon

from myapp.utils import Color, Page

# IMPORTANT : full_res=True pour utiliser le vrai 480x480
# (par défaut, Presto() utilise un framebuffer 240x240 mis à l'échelle !)

LARGEUR = 168
HAUTEUR = 80


class MyBtn:

    def __init__(self, x, y, w, h, name):
        self.name = name
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        self.w = w
        self.h = h

    def clicked(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def init_display(self, presto, display, vector):
        self.presto = presto
        self.display = display
        self.vector = vector
        self.btn = Polygon()
        self.btn.rectangle(self.x1,
                           self.y1,
                           self.w,
                           self.h,
                           corners=(10, 10, 10, 10))

    def affiche(self):
        self.display.set_pen(Color.LIGHTYELLOW)
        self.vector.draw(self.btn)
        self.display.set_pen(Color.BLACK)
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 28)
        pos = (LARGEUR - int(self.vector.measure_text(self.name)[2])) // 2
        self.vector.text(self.name, self.x1 + pos, self.y2 - 35)


BTN = {
    "temperatures": MyBtn(36, 60, LARGEUR, HAUTEUR, "Temperatures"),
    "horloge": MyBtn(256, 60, LARGEUR, HAUTEUR, "Horloge"),
    "switches": MyBtn(36, 150, LARGEUR, HAUTEUR, "Interrupteurs"),
    "flip": MyBtn(256, 150, LARGEUR, HAUTEUR, "Flip clock"),
    "mqttlogs": MyBtn(36, 240, LARGEUR, HAUTEUR, "Logs MQTT"),
    "calendrier": MyBtn(256, 240, LARGEUR, HAUTEUR, "Calendrier"),
    "alarme": MyBtn(36, 330, LARGEUR, HAUTEUR, "Alarmes"),
    "reboot": MyBtn(256, 330, LARGEUR, HAUTEUR, "Reboot"),
}


class Menu:

    def __init__(self, presto, display, vector, touch, mqtt, alerte, loggin):
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        self.mqtt = mqtt
        self.alerte = alerte
        if loggin is not None:
            loggin.log("Initialisation menu")
        for btn in BTN.values():
            btn.init_display(presto, display, vector)

    def affiche(self):
        self.display.set_pen(Color.BLACK)
        self.presto.clear()
        self.display.set_pen(Color.LIGHTYELLOW)
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 40)
        txt = "Choix page"
        lt = int(self.vector.measure_text(txt)[2])
        self.vector.text("Choix page", 240 - lt // 2, 35)
        for btn in BTN.values():
            btn.affiche()
        self.presto.update()
        page = Page.get_page()
        while True:
            self.mqtt.check_msg()
            if page != Page.get_page():
                return
            if self.alerte.id_show:
                self.alerte.show()
            gc.collect()
            self.touch.poll()
            if self.touch.state:
                while self.touch.state:
                    self.touch.poll()
                    time.sleep(.1)
                x, y = self.touch.x, self.touch.y
                for btn, coord in BTN.items():
                    if coord.clicked(x, y):
                        Page.set_page(btn)
                        return btn
            time.sleep(.1)


"""if __name__ == '__main__':
    presto = Presto(full_res=True)
    display = presto.display
    touch = presto.touch

    menu = Menu(presto, display, touch, None)
    print(menu.affiche())"""
