import gc
import time

import jpegdec

# IMPORTANT : full_res=True pour utiliser le vrai 480x480
# (par défaut, Presto() utilise un framebuffer 240x240 mis à l'échelle !)


class MyBtn:

    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def test(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2


IMG_MENU = "img/menu.jpg"
BTN = {
    "temperatures": MyBtn(36, 99, 225, 207),
    "horloge": MyBtn(256, 99, 417, 207),
    "switches": MyBtn(36, 226, 225, 333),
    "flip": MyBtn(253, 226, 417, 333),
    "mqttlogs": MyBtn(36, 359, 225, 466),
    "calendrier": MyBtn(253, 358, 417, 466),
}


class Menu:

    def __init__(self, presto, display, touch, loggin):
        self.presto = presto
        self.display = display
        self.touch = touch
        if loggin is not None:
            loggin.log("Initialisation menu")

    def affiche(self):
        self.img = jpegdec.JPEG(self.display)
        self.img.open_file(IMG_MENU)
        self.img.decode(0, 0, jpegdec.JPEG_SCALE_FULL)
        self.presto.update()
        while True:
            self.touch.poll()
            if self.touch.state:
                while self.touch.state:
                    self.touch.poll()
                    time.sleep(.1)
                x, y = self.touch.x, self.touch.y
                for btn, coord in BTN.items():
                    if coord.test(x, y):
                        del self.img
                        gc.collect()
                        return btn


if __name__ == '__main__':
    presto = Presto(full_res=True)
    display = presto.display
    touch = presto.touch

    menu = Menu(presto, display, touch, None)
    print(menu.affiche())
