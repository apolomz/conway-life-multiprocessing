# conway-life-multiprocessing

Sequential and parallel implementation of Conway's Game of Life in Python, featuring a GUI and performance analysis (speedup).

Proyecto del Parcial I para el curso de **Infraestructuras Paralelas y Distribuidas (750023C)** - Universidad del Valle (2026-2).

---

## Estructura del Proyecto

```text
conway-life-multiprocessing/
├── src/
│   ├── logic.py          # Lógica secuencial base e inicialización
│   ├── gui.py            # Interfaz gráfica (Pygame-CE)
│   └── parallel_logic.py # Motor paralelo (Threads + Barreras + SIMD)
├── benchmark.py          # Script de mediciones automáticas
├── main.py               # Punto de entrada principal
├── requirements.txt      # Dependencias del proyecto
└── README.md             # Documentación

# Instalar Dependencias

py -m pip install -r requirements.txt

## Iniciar:
 py main.py
 Modo secuencial:

 py main.py --secuencial

# Ejecutar pruebas:
py benchmark.py