import gc
import json
import time

from picovector import Polygon
from requests import get, post
from touch import Button

# from myapp.mqtt import set_callback
from myapp.secret import headers
from myapp.utils import PRISES, Color, Page, get_api, verifier_connexion

OFFSET = 70


class Switch:

    def __init__(self, display, vector, touch, mqtt, label, ligne,
                 initiale_state):
        self.display = display
        self.vector = vector
        self.touch = touch
        self.mqtt = mqtt
        self.label = label
        self.api = get_api()[0]
        self.switch = PRISES[label]
        self.capteur = "switch." + self.switch
        self.ligne = ligne
        self.on = Button(240, ligne * OFFSET, 100, 50)
        self.off = Button(360, ligne * OFFSET, 100, 50)
        self.state = initiale_state
        self.btn_on = Polygon()
        self.btn_on.rectangle(*self.on.bounds, corners=(10, 10, 10, 10))
        self.btn_off = Polygon()
        self.btn_off.rectangle(*self.off.bounds, corners=(10, 10, 10, 10))

    def get_state(self, maj):
        if not maj:
            return self.state
        url = self.api + "states/" + self.capteur
        try:
            response = get(url, headers=headers, timeout=1.2)
            result = json.loads(response.text)["state"]
            if result == "on":
                result = True
            elif result == "off":
                result = False
            else:  # unavalaible
                result = None
            try:
                response.close()
            except Exception:
                pass
        except Exception:
            result = None
        self.state = result
        return result

    def set_state(self, state):
        url = self.api + "services/switch/turn_" + ("on" if state else "off")
        data = {"entity_id": "switch." + self.switch}
        try:
            response = post(url, headers=headers, json=data)
            try:
                response.close()
            except Exception:
                self.state = None
        except Exception:
            self.state = None

    def update_state(self, state):
        self.state = state == 'on'

    def toggle(self):
        url = self.api + "services/switch/toggle"
        data = {"entity_id": "switch." + self.switch}
        try:
            response = post(url, headers=headers, json=data)
            try:
                response.close()
            except Exception:
                self.state = None
        except Exception:
            self.state = None

    def display_switch(self):
        self.display.set_pen(Color.GREY)
        self.vector.text(self.label, 10, self.ligne * OFFSET + 40)
        self.display.set_pen(Color.GREEN if self.state else Color.GREY)
        self.vector.draw(self.btn_on)
        self.display.set_pen(Color.RED if self.state is False else Color.GREY)
        self.vector.draw(self.btn_off)

    def wait_for_status(self, state):
        while self.state != state:
            self.state = self.get_state(True)
            time.sleep(0.1)

    def on_click(self):
        ret = False
        if self.on.is_pressed():  # and not self.state:
            self.mqtt.send_msg(self.label, "on")
            # self.set_state(True)
            ret = True
        elif self.off.is_pressed():  # and self.state:
            self.mqtt.send_msg(self.label, "off")
            # self.set_state(False)
            ret = True
        return ret


class Switches:
    switches = {}
    capteurs = []

    def __init__(self, presto, display, vector, touch, mqtt, loggin,
                 initiale_state):
        loggin.log("Initialisation switches")
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        self.mqtt = mqtt
        self.loggin = loggin
        self.api = get_api()[0]
        self.btnReturn = Button(360, 420, 100, 50)
        self.btn_exit = Polygon()
        self.btn_exit.rectangle(*self.btnReturn.bounds,
                                corners=(10, 10, 10, 10))
        ligne = 0
        for label, name in sorted(PRISES.items()):
            try:
                state = initiale_state["switch." + name]
            except KeyError:
                state = None
            self.switches[label] = Switch(display, vector, touch, mqtt, label,
                                          ligne, state)
            self.capteurs.append(self.switches[label].capteur)
            ligne += 1
        self.mqtt.set_callback(self.update_state)

    def on_click(self):
        """Retourne True si au moins un bouton cliqué"""
        ok = False
        for switch in self.switches:
            ok |= self.switches[switch].on_click()
        while self.touch.state:
            time.sleep(.1)
            self.touch.poll()
        return ok

    def update_state(self, topic, state):
        switch = self.mqtt.get_room(topic)
        if switch in self.switches:
            self.switches[switch].update_state(state)

    def get_state(self, switch, last):
        return self.switches[switch].get_state(last)

    def get_all_states(self):
        """Récupération de l'enseble des états en 1 demande"""
        url = self.api + "states"
        try:
            response = get(url, headers=headers, timeout=2.0)
            states = response.json()
            # Extraction des données
            switch_states = {
                s["entity_id"]: s["state"]
                for s in states if s["entity_id"] in self.capteurs
            }
            # Mise à jour des switches
            for key in self.switches:
                result = switch_states[self.switches[key].capteur]
                if result == "on":
                    result = True
                elif result == "off":
                    result = False
                    """Récupération de l'enseble des états en 1 demande"""
                else:  # unavalaible
                    result = None
                self.switches[key].state = result
            try:
                response.close()
            except Exception:
                pass
        except Exception:
            result = None

    def update_screen(self):
        self.display.set_pen(Color.BLACK)
        self.display.clear()
        for switch in self.switches:
            self.switches[switch].display_switch()
        self.display.set_pen(Color.CYAN)
        self.vector.draw(self.btn_exit)
        self.display.set_pen(Color.BLACK)
        self.vector.text("Exit", 383, 457)
        self.presto.update()
        gc.collect()

    def affiche(self):
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 38)
        self.update_screen()
        cmpt = 1
        while True:
            verifier_connexion(self.presto, self.loggin)
            if Page.get_page() != 'switches':
                return
            self.mqtt.check_msg()
            self.touch.poll()
            if self.btnReturn.is_pressed():
                self.display.set_pen(Color.BLACK)
                self.display.clear()
                Page.set_page('horloge')
                return
            elif self.on_click() or cmpt % 15 == 0:
                self.update_screen()
            cmpt += 1
            time.sleep(0.1)
