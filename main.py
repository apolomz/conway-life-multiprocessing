import sys
from src.gui import ejecutar_gui

if __name__ == "__main__":
    modo_ejecucion = "secuencial" if "--secuencial" in sys.argv else "paralelo"
    ejecutar_gui(modo=modo_ejecucion)