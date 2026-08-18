import time

from myapp.utils import MOIS, TZ, Color


def is_leap_year(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def days_in_month(year, month):
    if month == 2:
        return 29 if is_leap_year(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def prev_month(year, month):
    if month == 1:
        return year - 1, 12
    return year, month - 1


def next_month(year, month):
    if month == 12:
        return year + 1, 1
    return year, month + 1


def weekday(year, month, day):
    # 0 = lundi, 6 = dimanche
    if month < 3:
        month += 12
        year -= 1
    k = year % 100
    j = year // 100
    h = (day + (13 * (month + 1)) // 5 + k + k // 4 + j // 4 + 5 * j) % 7
    return (h + 5) % 7


def add_days(year, month, day, delta):
    while delta > 0:
        dim = days_in_month(year, month)
        if day + delta <= dim:
            day += delta
            delta = 0
        else:
            delta -= dim - day + 1
            year, month = next_month(year, month)
            day = 1

    while delta < 0:
        if day + delta >= 1:
            day += delta
            delta = 0
        else:
            delta += day
            year, month = prev_month(year, month)
            day = days_in_month(year, month)

    return year, month, day


def iso_week_number(year, month, day):
    # Numéro ISO 8601 basé sur le jeudi de la semaine
    wday = weekday(year, month, day)
    y, m, d = add_days(year, month, day, 3 - wday)  # jeudi de la semaine

    jan4_wday = weekday(y, 1, 4)
    week1_monday_y, week1_monday_m, week1_monday_d = add_days(
        y, 1, 4, -jan4_wday)

    days = 0
    cy, cm, cd = week1_monday_y, week1_monday_m, week1_monday_d
    while (cy, cm, cd) != (y, m, d):
        cy, cm, cd = add_days(cy, cm, cd, 1)
        days += 1

    return 1 + days // 7


def monthly_calendar(year, month):
    month_days = days_in_month(year, month)
    first_wday = weekday(year, month, 1)

    result = []
    result.append(["", "lun", "mar", "mer", "jeu", "ven", "sam", "dim"])

    py, pm = prev_month(year, month)
    prev_days = days_in_month(py, pm)

    day = 1
    start_day = prev_days - first_wday + 1

    # Trouver le lundi de la première ligne
    if first_wday == 0:
        line_year, line_month, line_day = year, month, 1
    else:
        line_year, line_month, line_day = py, pm, start_day

    while True:
        week = [str(iso_week_number(line_year, line_month, line_day))]
        cy, cm, cd = line_year, line_month, line_day

        for i in range(7):
            if (cy, cm, cd) == (year, month, day) and day <= month_days:
                week.append(str(day))
                day += 1
            else:
                week.append(str(cd))
            cy, cm, cd = add_days(cy, cm, cd, 1)

        result.append(week)

        # Arrêt quand on a dépassé le mois et fini la semaine courante
        if day > month_days and (cy, cm) != (year, month):
            break

        line_year, line_month, line_day = cy, cm, cd

    return result


class Calendar:

    def __init__(self, presto, display, vector, touch):
        self.presto = presto
        self.display = display
        self.vector = vector
        self.touch = touch
        s = time.time()
        offset = 3600 * TZ.get_offset(s)
        self.ny, self.nm, d, _, _, _, _, _ = time.gmtime(s + offset)
        self.year = self.ny
        self.month = self.nm
        self.mday = d  # Utilisé pour la surbrillance de la date courante
        self.calendar = monthly_calendar(self.year, self.month)
        # Initialisation de l'affichage

    def set_year(self, year):
        self.year = year
        self.calendar = monthly_calendar(self.year, self.month)

    def set_month(self, month):
        self.month = month
        self.calendar = monthly_calendar(self.year, self.month)

    def draw_calendar(self):
        self.display.set_pen(Color.BLACK)
        self.display.clear()
        # Dessin du calendrier
        self.display.set_pen(Color.CYAN)
        self.display.rectangle(12, 70, 460, 354)
        self.display.rectangle(13, 71, 458, 352)
        self.display.set_pen(Color.GREY)
        self.display.rectangle(14, 72, 456, 350)
        self.display.set_pen(Color.CYAN)
        # 1 ligne vertical tous les 58 pixels
        for x in range(70, 423, 57):
            self.display.line(x, 72, x, 422)
        # 1 ligne horizontale tous les 50 pixels
        for y in range(123, 374, 50):
            self.display.line(14, y, 470, y)
        # Affichage du text
        self.display.set_pen(Color.GREY)
        s = f"{MOIS[self.month - 1]} {self.year}"
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 48)
        x = int((480 - self.vector.measure_text(s)[2]) // 2)
        self.vector.text(s, x, 48)
        self.vector.set_font("Roboto-Medium-With-Material-Symbols.af", 32)
        self.display.set_pen(Color.BLACK)
        y = 110
        i = 0
        for line in self.calendar:
            x = 16
            first = True
            for s in line:
                if first:
                    first = False
                    self.display.set_pen(Color.ORANGE)
                else:
                    if s == "1" and x != 14:
                        i += 1
                    if i == 1 or y == 110:
                        if str(
                                self.mday
                        ) == s and self.year == self.ny and self.month == self.nm:
                            self.display.set_pen(Color.ORANGE)
                        else:
                            self.display.set_pen(Color.BLACK)
                    else:
                        self.display.set_pen(Color.DARKGREY)
                l = int((50 - self.vector.measure_text(s)[2]) // 2)
                self.vector.text(s, x + l, y)
                x += 57
            y += 50
        self.presto.update()

    def affiche(self):
        while self.touch.state:
            self.touch.poll()
        self.draw_calendar()
        lh = list(map(int, self.vector.measure_text("##:##:##")))
        last_time = 0
        while True:
            self.touch.poll()
            if self.touch.state:
                if self.touch.y > 400:
                    return
                xs, ys = self.touch.x, self.touch.y
                while self.touch.state:
                    self.touch.poll()
                dx, dy = xs - self.touch.x, ys - self.touch.y
                if abs(dx) < abs(dy):
                    if dy > 0:
                        self.set_year(self.year + 1)
                    else:
                        self.set_year(self.year - 1)
                else:
                    if dx > 0:
                        self.set_month(self.month + 1)
                    else:
                        self.set_month(self.month - 1)
                self.draw_calendar()
            s = time.time()
            offset = 3600 * TZ.get_offset(s)
            if last_time == s:
                time.sleep(0.1)
                continue
            _, _, _, hour, minute, second, _, _ = time.gmtime(s + offset)
            heure = f"{hour:02d}:{minute:02d}:{second:02d}"
            self.display.set_pen(Color.BLACK)
            self.display.rectangle(96, 430, 304, 479)
            self.display.set_pen(Color.GREY)
            self.vector.text(heure, (480 - lh[2]) // 2, 465)
            self.presto.update()
