# Conway: Vida en Paralelo

Proyecto del Parcial I de **Infraestructuras Paralelas y Distribuidas (750023C)**, Universidad del Valle, periodo 2026-2.

Implementa el Juego de la Vida de Conway con cálculo secuencial y paralelo, y una interfaz gráfica en Pygame para configurar, preparar y ejecutar simulaciones.

## Estructura

```text
conway-life-multiprocessing/
├── Gui/                         # Aplicación Pygame
│   └── gui/
│       ├── screens/             # Menú, preparación y simulación
│       ├── models/              # Estado y representación del tablero
│       ├── app.py               # Ciclo de vida de la aplicación
│       ├── components.py        # Componentes reutilizables
│       ├── simulation_engine.py # Adaptador a los motores del proyecto
│       └── theme.py             # Colores y utilidades visuales
├── src/
│   ├── logic.py                 # Reglas e inicialización del tablero
│   └── parallel_logic.py        # Cálculo paralelo con hilos y NumPy
├── benchmark.py                 # Medición de rendimiento
├── main.py                      # Punto de entrada
└── requirements.txt             # Dependencias
```

## Requisitos e instalación

Se requiere Python 3.10 o posterior. Desde la raíz del proyecto, instala las dependencias con:

```bash
python -m pip install -r requirements.txt
```

## Iniciar la aplicación

Desde la raíz del proyecto:

```bash
python main.py
```

También puedes iniciar la GUI directamente:

```bash
python Gui/run.py
```

## Uso de la interfaz

El menú principal permite iniciar una simulación, consultar una explicación breve del Juego de la Vida o salir.

En **Preparar simulación** puedes:

- Configurar filas y columnas manualmente o elegir tableros de 100×100, 500×500 y 1000×1000.
- Seleccionar ejecución secuencial o paralela y configurar el número de hilos para el modo paralelo.
- Editar las células: clic izquierdo para alternar una célula, arrastrar para pintar y clic derecho para borrar.
- Generar un estado inicial aleatorio con 20% de células vivas o limpiar el tablero.
- Acercar o alejar con la rueda del ratón. Usa las flechas o WASD para mover la vista y el minimapa para saltar a otra zona del tablero.
- Revisar las filas, columnas y nivel de zoom visibles, además del número de células vivas.

Pulsa **Iniciar simulación** para ejecutar el estado preparado. En la pantalla de simulación puedes pausar o continuar, avanzar una generación, reiniciar al estado inicial y ajustar la velocidad entre 1 y 30 generaciones por segundo. El panel **Controles** muestra los atajos: espacio para pausar o continuar, rueda para zoom, flechas o WASD para mover la vista y clic en el minimapa para navegar. La pantalla también muestra el tamaño y modo elegidos, la generación actual y las células vivas.

Los colores de la interfaz son monocromáticos. La vista del tablero está desplazable y ampliable para facilitar la edición y observación de matrices grandes.

## Benchmark

Desde la raíz del proyecto:

```bash
python benchmark.py
```

El benchmark compara los motores secuencial y paralelo para distintos tamaños de matriz y cantidades de hilos, valida que los resultados coincidan y genera `grafica_speedup.png`.
