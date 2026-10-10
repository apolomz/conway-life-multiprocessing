
import threading
import numpy as np


_tablero_actual_global = None
_tablero_siguiente_global = None



def _calcular_bloque_vectorizado(tablero, fila_inicio, fila_fin):
    """Calcula un bloque de filas con NumPy """
    total_filas, total_columnas = tablero.shape
    altura = fila_fin - fila_inicio

    if altura == 0 or total_filas == 0:
        return np.zeros(
            (altura, total_columnas),
            dtype=np.uint8
        )

    filas_salida = np.arange(fila_inicio, fila_fin)

    vecinos = np.zeros(
        (altura, total_columnas),
        dtype=np.uint8
    )

    # Cada combinación representa uno de los ocho vecinos
    for desplazamiento_fila in (-1, 0, 1):
        filas_vecinas = (
            filas_salida + desplazamiento_fila
        ) % total_filas

        bloque_filas = tablero[filas_vecinas, :]

        for desplazamiento_columna in (-1, 0, 1):

            if (
                desplazamiento_fila == 0
                and desplazamiento_columna == 0
            ):
                continue

            # El desplazamiento circular reproduce el toroide
            vecinos += np.roll(
                bloque_filas,
                shift=-desplazamiento_columna,
                axis=1
            )

    celdas_actuales = tablero[fila_inicio:fila_fin, :]

    sobreviven = (
        (celdas_actuales == 1)
        & ((vecinos == 2) | (vecinos == 3))
    )

    nacen = (
        (celdas_actuales == 0)
        & (vecinos == 3)
    )

    return (sobreviven | nacen).astype(np.uint8)



def _trabajador_hilo(
    id_hilo,
    fila_inicio,
    fila_fin,
    barrera,
    total_generaciones
):
    global _tablero_actual_global, _tablero_siguiente_global

    for _ in range(total_generaciones):

        # Todos leen el tablero actual, pero cada hilo escribe
        # exclusivamente en sus propias filas del tablero siguiente.
        tablero_actual = _tablero_actual_global

        resultado = _calcular_bloque_vectorizado(
            tablero_actual,
            fila_inicio,
            fila_fin
        )

        _tablero_siguiente_global[fila_inicio:fila_fin, :] = resultado

        # Esperar a que todos terminen de calcular.
        barrera.wait()

        # Un solo hilo intercambia los dos tableros.
        if id_hilo == 0:
            (
                _tablero_actual_global,
                _tablero_siguiente_global
            ) = (
                _tablero_siguiente_global,
                _tablero_actual_global
            )

        # Nadie empieza la siguiente generación antes del intercambio.
        barrera.wait()


def _ejecutar_paralelo(tablero_inicial, num_hilos, generaciones):
    global _tablero_actual_global, _tablero_siguiente_global

    if num_hilos < 1:
        raise ValueError("num_hilos debe ser mayor que cero")

    if generaciones < 0:
        raise ValueError("generaciones no puede ser negativo")

    _tablero_actual_global = np.asarray(
        tablero_inicial,
        dtype=np.uint8
    ).copy()

    _tablero_siguiente_global = np.zeros_like(
        _tablero_actual_global
    )

    total_filas = _tablero_actual_global.shape[0]

    if total_filas == 0:
        return _tablero_actual_global.copy()

    num_hilos = min(num_hilos, total_filas)

    filas_por_hilo = total_filas // num_hilos
    barrera = threading.Barrier(num_hilos)
    hilos = []

    for i in range(num_hilos):
        fila_inicio = i * filas_por_hilo

        fila_fin = (
            total_filas
            if i == num_hilos - 1
            else (i + 1) * filas_por_hilo
        )

        hilo = threading.Thread(
            target=_trabajador_hilo,
            args=(
                i,
                fila_inicio,
                fila_fin,
                barrera,
                generaciones
            )
        )

        hilos.append(hilo)
        hilo.start()

    for hilo in hilos:
        hilo.join()

    return _tablero_actual_global.copy()


def calcular_sig_gen(tablero_actual, num_hilos=4):
    """Calcula una generación para la interfaz gráfica."""
    return _ejecutar_paralelo(
        tablero_actual,
        num_hilos,
        generaciones=1
    )


def ejecutar_bloque_paralelo_multigen(
    tablero_inicial,
    num_hilos=4,
    generaciones=100
):
    """Ejecuta varias generaciones con los mismos hilos."""
    return _ejecutar_paralelo(
        tablero_inicial,
        num_hilos,
        generaciones
    )
