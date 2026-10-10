
import time
import matplotlib.pyplot as plt
import numpy as np

from src.logic import (
    inicializar_tablero,
    calcular_siguiente_generacion,
)

from src.parallel_logic import ejecutar_bloque_paralelo_multigen


def benchmark():
    tamanos = [100, 500, 1000]
    num_hilos_lista = [1, 2, 4, 8]
    generaciones = 20

    resultados = {tam: {} for tam in tamanos}

    print("INICIANDO MEDICION DE RENDIMIENTO\n")

    for tam in tamanos:
        print(
            f"=== Matriz {tam}x{tam} "
            f"({generaciones} generaciones) ==="
        )

        # Un mismo tablero inicial para todas las comparaciones.
        tablero_base = inicializar_tablero(tam, tam)

        # Medir la implementación secuencial original.
        t_inicio = time.perf_counter()

        tablero_secuencial = tablero_base.copy()

        for _ in range(generaciones):
            tablero_secuencial = calcular_siguiente_generacion(
                tablero_secuencial
            )

        t_secuencial = time.perf_counter() - t_inicio

        print(f"  Secuencial: {t_secuencial:.4f} s")

        # Medir la implementación paralela con varios hilos.
        for hilos in num_hilos_lista:
            t_inicio = time.perf_counter()

            tablero_paralelo = ejecutar_bloque_paralelo_multigen(
                tablero_base,
                num_hilos=hilos,
                generaciones=generaciones,
            )

            t_paralelo = time.perf_counter() - t_inicio

            # Verificar que ambos algoritmos produzcan el mismo resultado.
            if not np.array_equal(
                tablero_secuencial,
                tablero_paralelo
            ):
                raise AssertionError(
                    f"ERROR: los tableros no coinciden para "
                    f"{tam}x{tam} con {hilos} hilos."
                )

            # Speedup = tiempo secuencial / tiempo paralelo.
            speedup = t_secuencial / t_paralelo
            resultados[tam][hilos] = speedup

            print(
                f"  Paralelo ({hilos} hilos): "
                f"{t_paralelo:.4f} s | "
                f"Speedup: {speedup:.2f}x"
            )

        print("  Verificación: todos los resultados coinciden.\n")

    # Generar y guardar la gráfica de speedup.
    plt.figure(figsize=(9, 5))

    for tam in tamanos:
        speedups = [
            resultados[tam][h]
            for h in num_hilos_lista
        ]

        plt.plot(
            num_hilos_lista,
            speedups,
            marker="o",
            label=f"Matriz {tam}x{tam}",
        )

    # Speedup ideal de referencia: S(p) = p.
    plt.plot(
        num_hilos_lista,
        num_hilos_lista,
        "k--",
        alpha=0.5,
        label="Ideal (Lineal)",
    )

    # Sin aceleración respecto al secuencial.
    plt.axhline(
        y=1,
        color="gray",
        linestyle=":",
        alpha=0.8,
        label="Sin aceleración (1x)",
    )

    plt.title("Aceleración (Speedup) vs. Número de Hilos")
    plt.xlabel("Número de Hilos")
    plt.ylabel("Speedup (T_sec / T_par)")
    plt.xticks(num_hilos_lista)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig("grafica_speedup.png", dpi=300)
    plt.close()

    print("Gráfica 'grafica_speedup.png' generada con éxito.")


if __name__ == "__main__":
    benchmark()
