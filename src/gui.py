import pygame
import os
from src.logic import (
    CANTIDAD_FILAS,
    CANTIDAD_COLUMNAS,
    TAMANO_CELDA_PIXELES,
    ANCHO_VENTANA,
    ALTO_VENTANA,
    FOTOGRAMAS_POR_SEGUNDO,
    COLOR_FONDO,
    COLOR_CELULA_VIVA,
    inicializar_tablero,
    calcular_siguiente_generacion
)
from src.parallel_logic import calcular_sig_gen

def ejecutar_gui(modo="paralelo"):
    pygame.init()

    if os.path.exists("python.png"):
        icono_aplicacion = pygame.image.load("python.png")
        pygame.display.set_icon(icono_aplicacion)

    pantalla_grafica = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption(f"La Vida - Versión {modo.capitalize()}")
    reloj_sistema = pygame.time.Clock()

    tablero = inicializar_tablero(CANTIDAD_FILAS, CANTIDAD_COLUMNAS)
    juego_en_ejecucion = True
    simulacion_pausada = False

    while juego_en_ejecucion:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                juego_en_ejecucion = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    simulacion_pausada = not simulacion_pausada
                elif evento.key == pygame.K_r:
                    tablero = inicializar_tablero(CANTIDAD_FILAS, CANTIDAD_COLUMNAS)

        if not simulacion_pausada:
            if modo == "paralelo":
                tablero = calcular_sig_gen(tablero, num_hilos=4)
            else:
                tablero = calcular_sig_gen(tablero)

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