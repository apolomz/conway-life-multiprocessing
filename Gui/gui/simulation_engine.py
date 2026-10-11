from __future__ import annotations

import numpy as np

from .models.board_state import BoardState
from src.logic import calcular_siguiente_generacion
from src.parallel_logic import calcular_sig_gen


class SimulationEngine:
    """Calculate one generation using the selected project implementation."""

    def next_generation(self, board: BoardState, mode: str, workers: int) -> BoardState:
        current = np.frombuffer(board.cells, dtype=np.uint8).reshape(board.rows, board.columns).copy()
        if mode == "sequential":
            result = calcular_siguiente_generacion(current)
        elif mode == "parallel":
            result = calcular_sig_gen(current, num_hilos=workers)
        else:
            raise ValueError(f"Modo de ejecución desconocido: {mode}")

        result = np.asarray(result, dtype=np.uint8)
        next_board = BoardState(board.rows, board.columns)
        next_board.cells = bytearray(result.reshape(-1).tobytes())
        next_board.alive_count = int(np.count_nonzero(result))
        return next_board
