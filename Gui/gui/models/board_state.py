from __future__ import annotations

class BoardState:
    """Store cells in a byte array so even a 1000×1000 board stays compact."""

    def __init__(self, rows: int, columns: int) -> None:
        self.rows = rows
        self.columns = columns
        self.cells = bytearray(rows * columns)
        self.alive_count = 0

    def is_alive(self, row: int, column: int) -> bool:
        return bool(self.cells[row * self.columns + column])

    def set_alive(self, row: int, column: int, alive: bool) -> None:
        if not (0 <= row < self.rows and 0 <= column < self.columns):
            return
        index = row * self.columns + column
        previous = self.cells[index]
        next_value = int(alive)
        if previous != next_value:
            self.cells[index] = next_value
            self.alive_count += 1 if next_value else -1

    def toggle(self, row: int, column: int) -> None:
        if 0 <= row < self.rows and 0 <= column < self.columns:
            self.set_alive(row, column, not self.is_alive(row, column))

    def clear(self) -> None:
        self.cells = bytearray(self.rows * self.columns)
        self.alive_count = 0

    def load_matrix(self, matrix) -> None:
        """Replace the board contents with a matrix produced by the project logic."""
        if matrix.shape != (self.rows, self.columns):
            raise ValueError(
                f"La matriz debe tener dimensiones {(self.rows, self.columns)}; "
                f"se recibió {matrix.shape}."
            )
        self.cells = bytearray(matrix.astype("uint8", copy=False).reshape(-1).tobytes())
        self.alive_count = int(matrix.sum())

    def copy(self) -> "BoardState":
        duplicate = BoardState(self.rows, self.columns)
        duplicate.cells = bytearray(self.cells)
        duplicate.alive_count = self.alive_count
        return duplicate
