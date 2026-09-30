import presto
from picovector import ANTIALIAS_BEST, PicoVector

from myapp.utils import (
    Color,
    Log,
)
from myapp.version import __version__

# Initialisation générale
presto = presto.Presto(full_res=True)
display = presto.display
touch = presto.touch
vector = PicoVector(display)
vector.set_antialiasing(ANTIALIAS_BEST)
Color.init(display)
loggin = Log(presto, display, vector, f"tsttouch - {__version__}")
loggin.log("Lancement application")

# bg = Color.BLACK
# fg = Color.WHITE

# Initialistion des objets

# Boucle de traitement de l'affichage
while True:
    touch.poll()
    state = touch.state
    if state:
        x, y = touch.x, touch.y
        loggin.log(f"touch : x={x} y={y}")
