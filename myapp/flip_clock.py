import gc
import time

from picovector import Polygon
from touch import Button

from myapp.utils import TZ, Color, Page

# Constants
MONTHS = (
    "",
    "JANV",
    "FEVR",
    "MARS",
    "AVRI",
    "MAI",
    "JUIN",
    "JUIL",
    "AOUT",
    "SEPT",
    "OCTO",
    "NOVE",
    "DECE",
)
DAYS = ("LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI", "SAMEDI",
        "DIMANCHE")


class Flip_Clock:
    WIDTH, HEIGHT = 480, 480
    CX, CY = 240, 240
    dark = False

    def __init__(self, presto, display, vector, touch, mqtt):
        self.display = display
        self.presto = presto
        self.vector = vector
        self.touch = touch
        self.mqtt = mqtt

        # Make background as a button (so you can tap anywhere), used to switch between dark/light mode
        self.bg = Button(0, 360, self.WIDTH, self.HEIGHT)
        self.BG_COLOR = Color.BLACK

        # Set up boxes with rounded corners and lines in the middle for the "flips"
        margin = 10
        self.big_box_size = 200

        self.hour_box_x = self.CX - self.big_box_size - margin
        self.hour_box_y = margin * 2
        self.hour_box = Polygon()
        self.hour_box.rectangle(
            self.hour_box_x,
            self.hour_box_y,
            self.big_box_size,
            self.big_box_size,
            (20, 20, 20, 20),
        )
        # print(f"{self.hour_box_x} {self.hour_box_y} {self.big_box_size}")
        self.hour_line_y = self.hour_box_y + (self.big_box_size // 2)
        self.hour_line = Polygon()
        self.hour_line.line(
            self.hour_box_x,
            self.hour_line_y,
            self.hour_box_x + self.big_box_size,
            self.hour_line_y,
            3,
        )

        self.minute_box_x = self.CX + margin
        self.minute_box_y = self.hour_box_y
        self.minute_box = Polygon()
        self.minute_box.rectangle(
            self.minute_box_x,
            self.minute_box_y,
            self.big_box_size,
            self.big_box_size,
            (20, 20, 20, 20),
        )
        self.minute_line_y = self.minute_box_y + (self.big_box_size // 2)
        self.minute_line = Polygon()
        self.minute_line.line(
            self.minute_box_x,
            self.minute_line_y,
            self.minute_box_x + self.big_box_size,
            self.minute_line_y,
            3,
        )

        self.small_box_size = 100

        self.week_day_box_width = 400
        self.week_day_box_x = (self.WIDTH - self.week_day_box_width) // 2
        self.week_day_box_y = self.hour_box_y + self.big_box_size + margin * 2
        self.week_day_box = Polygon()
        self.week_day_box.rectangle(
            self.week_day_box_x,
            self.week_day_box_y,
            self.week_day_box_width,
            self.small_box_size,
            (10, 10, 10, 10),
        )
        self.week_day_line_y = self.week_day_box_y + (self.small_box_size // 2)
        self.week_day_line = Polygon()
        self.week_day_line.line(
            self.week_day_box_x,
            self.week_day_line_y,
            self.week_day_box_x + self.week_day_box_width,
            self.week_day_line_y,
            2,
        )

        self.month_box_width = 200
        self.day_box_x = (self.WIDTH - self.small_box_size -
                          self.month_box_width) // 2
        self.day_box_y = self.week_day_box_y + self.small_box_size + margin * 2
        self.day_box = Polygon()
        self.day_box.rectangle(
            self.day_box_x,
            self.day_box_y,
            self.small_box_size,
            self.small_box_size,
            (10, 10, 10, 10),
        )
        self.day_line_y = self.day_box_y + (self.small_box_size // 2)
        self.day_line = Polygon()
        self.day_line.line(
            self.day_box_x,
            self.day_line_y,
            self.day_box_x + self.small_box_size,
            self.day_line_y,
            2,
        )

        self.month_box_x = self.day_box_x + self.small_box_size + margin
        self.month_box_y = self.day_box_y
        self.month_box = Polygon()
        self.month_box.rectangle(
            self.month_box_x,
            self.month_box_y,
            self.month_box_width,
            self.small_box_size,
            (10, 10, 10, 10),
        )
        self.month_line_y = self.month_box_y + (self.small_box_size // 2)
        self.month_line = Polygon()
        self.month_line.line(
            self.month_box_x,
            self.month_line_y,
            self.month_box_x + self.month_box_width,
            self.month_line_y,
            2,
        )

    def draw(self):
        self.display.set_pen(self.BG_COLOR)
        self.display.clear()

        self.display.set_pen(Color.LIGHTYELLOW)
        self.vector.draw(self.hour_box)
        self.vector.draw(self.minute_box)
        self.vector.draw(self.week_day_box)
        self.vector.draw(self.day_box)
        self.vector.draw(self.month_box)

        s = time.time()
        _, month, day, hour, minute, _, week_day, _ = time.localtime(
            s + TZ.get_offset(s) * 3600)

        self.display.set_pen(Color.BLACK)
        self.vector.set_font("Roboto-Bold.af", 150)
        # vector text seems to render a bit weirdly vertically, need this offset (found by trial and error)
        text_offset_y = 140

        hour_text = f"{hour}"
        _, _, hour_text_width, _ = self.vector.measure_text(hour_text)
        hour_text_x = self.hour_box_x + (
            (self.big_box_size - int(hour_text_width)) // 2)
        self.vector.text(hour_text, hour_text_x,
                         self.hour_box_y + text_offset_y)

        minute_text = f"{minute:02d}"
        _, _, minute_text_width, _ = self.vector.measure_text(minute_text)
        self.vector.text(
            minute_text,
            self.minute_box_x +
            ((self.big_box_size - int(minute_text_width)) // 2),
            self.minute_box_y + text_offset_y,
        )

        self.vector.set_font_size(70)
        text_offset_y = 70

        week_day_text = DAYS[week_day]
        _, _, week_day_text_width, _ = self.vector.measure_text(week_day_text)
        self.vector.text(
            week_day_text,
            self.week_day_box_x +
            ((self.week_day_box_width - int(week_day_text_width)) // 2),
            self.week_day_box_y + text_offset_y,
        )

        day_text = f"{day}"
        _, _, day_text_width, _ = self.vector.measure_text(day_text)
        self.vector.text(
            day_text,
            self.day_box_x +
            ((self.small_box_size - int(day_text_width)) // 2),
            self.day_box_y + text_offset_y,
        )

        month_text = MONTHS[month]
        _, _, month_text_width, _ = self.vector.measure_text(month_text)
        self.vector.text(
            month_text,
            self.month_box_x +
            ((self.month_box_width - int(month_text_width)) // 2),
            self.month_box_y + text_offset_y,
        )

        self.display.set_pen(Color.BLACK)
        self.vector.draw(self.hour_line)
        self.vector.draw(self.minute_line)
        self.vector.draw(self.week_day_line)
        self.vector.draw(self.day_line)
        self.vector.draw(self.month_line)

        self.presto.update()
        gc.collect()

    def affiche(self):
        time.sleep(1)
        while True:
            self.mqtt.check_msg()
            if Page.page != 'flip':
                return
            self.touch.poll()
            if self.bg.is_pressed():
                self.display.set_pen(Color.BLACK)
                self.display.clear()
                Page.set_page('horloge')
                return
            self.draw()
            time.sleep(1)
