import numpy as np
import pygame


# CONFIGURACIÓN DEL JUEGO Y DIMENSIONES
CANTIDAD_FILAS = 100
CANTIDAD_COLUMNAS = 100
TAMANO_CELDA_PIXELES = 8

ANCHO_VENTANA = CANTIDAD_COLUMNAS * TAMANO_CELDA_PIXELES
ALTO_VENTANA = CANTIDAD_FILAS * TAMANO_CELDA_PIXELES
FOTOGRAMAS_POR_SEGUNDO = 15

# PALETA DE COLORES (FORMATO RGB)
COLOR_FONDO = (10, 10, 15)                # Color de las células muertas y fondo
COLOR_CELULA_VIVA = (0, 255, 128)          # Color de las células vivas
COLOR_CUADRICULA = (30, 30, 40)            # Color de las líneas divisorias


# INICIALIZACIÓN DEL TABLERO
def inicializar_tablero(total_filas, total_columnas, probabilidad_viva=0.2):
    """
    Crea una matriz con valores booleanos/enteros (0 o 1).
    0 representa célula muerta y 1 representa célula viva.
    """
    probabilidad_muerta = 1.0 - probabilidad_viva
    distribucion_probabilidad = [probabilidad_muerta, probabilidad_viva]

    tablero_inicial = np.random.choice(
        [0, 1],
        size=(total_filas, total_columnas),
        p=distribucion_probabilidad
    )
    return tablero_inicial


# LÓGICA DE VECINDARIO Y REGLAS DE CONWAY

def contar_vecinos_vivos(tablero, fila_actual, columna_actual, total_filas, total_columnas):
    """
    Calcula cuántos vecinos vivos rodean a una celda específica.
    Implementa un toroide (bordes continuos mediante el operador residuo/módulo).
    """
    cantidad_vecinos_vivos = 0

    desplazamientos = (-1, 0, 1)
    for desplazamiento_fila in desplazamientos:
        for desplazamiento_columna in desplazamientos:
            # Excluir la propia célula que se está evaluando
            if desplazamiento_fila == 0 and desplazamiento_columna == 0:
                continue

            fila_vecina = (fila_actual + desplazamiento_fila) % total_filas
            columna_vecina = (columna_actual + desplazamiento_columna) % total_columnas

            cantidad_vecinos_vivos += tablero[fila_vecina, columna_vecina]

    return cantidad_vecinos_vivos


def calcular_siguiente_generacion(tablero_actual):
    """
    Aplica las reglas clásicas del Juego de la Vida de Conway:
    1. Célula viva con menos de 2 vecinos muere por soledad.
    2. Célula viva con 2 o 3 vecinos sobrevive.
    3. Célula viva con más de 3 vecinos muere por sobrepoblación.
    4. Célula muerta con exactamente 3 vecinos nace.
    """
    total_filas, total_columnas = tablero_actual.shape
    tablero_siguiente = np.zeros((total_filas, total_columnas), dtype=np.int8)

    for fila in range(total_filas):
        for columna in range(total_columnas):
            vecinos_vivos = contar_vecinos_vivos(
                tablero_actual,
                fila,
                columna,
                total_filas,
                total_columnas
            )
            estado_celula = tablero_actual[fila, columna]

            if estado_celula == 1:
                # Célula viva sobrevive con 2 o 3 vecinos
                if vecinos_vivos == 2 or vecinos_vivos == 3:
                    tablero_siguiente[fila, columna] = 1
                else:
                    tablero_siguiente[fila, columna] = 0
            else:
                # Célula muerta nace únicamente con 3 vecinos
                if vecinos_vivos == 3:
                    tablero_siguiente[fila, columna] = 1

    return tablero_siguiente


# BUCLE PRINCIPAL CON INTERFAZ GRÁFICA
def main():
    pygame.init()

    #icono personalizado en formato PNG
    icono_aplicacion = pygame.image.load("python.png")
    pygame.display.set_icon(icono_aplicacion)
    # Configuración de la ventana gráfica
    pantalla_grafica = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("La Vida - Versión Secuencial")
    reloj_sistema = pygame.time.Clock()

    tablero = inicializar_tablero(CANTIDAD_FILAS, CANTIDAD_COLUMNAS)
    juego_en_ejecucion = True
    simulacion_pausada = False

    while juego_en_ejecucion:
        # Gestión de eventos de entrada (teclado y ventana)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                juego_en_ejecucion = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    simulacion_pausada = not simulacion_pausada
                elif evento.key == pygame.K_r:
                    tablero = inicializar_tablero(CANTIDAD_FILAS, CANTIDAD_COLUMNAS)

        # Actualización lógica del juego
        if not simulacion_pausada:
            tablero = calcular_siguiente_generacion(tablero)

        # Renderizado gráfico
        pantalla_grafica.fill(COLOR_FONDO)

        for fila in range(CANTIDAD_FILAS):
            for columna in range(CANTIDAD_COLUMNAS):
                if tablero[fila, columna] == 1:
                    posicion_x = columna * TAMANO_CELDA_PIXELES
                    posicion_y = fila * TAMANO_CELDA_PIXELES
                    ancho_rectangulo = TAMANO_CELDA_PIXELES - 1
                    alto_rectangulo = TAMANO_CELDA_PIXELES - 1

                    pygame.draw.rect(
                        pantalla_grafica,
                        COLOR_CELULA_VIVA,
                        (posicion_x, posicion_y, ancho_rectangulo, alto_rectangulo)
                    )

        pygame.display.flip()
        reloj_sistema.tick(FOTOGRAMAS_POR_SEGUNDO)

    pygame.quit()


if __name__ == "__main__":
    main()