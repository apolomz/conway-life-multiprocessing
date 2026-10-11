"""Board editor with a clipped, zoomable viewport for large matrices."""

from __future__ import annotations

import pygame

from .. import theme
from ..components import Button
from ..models.board_state import BoardState
from .settings import SimulationSettings
from src.logic import inicializar_tablero


class BoardPreparation:
    MIN_CELL_SIZE = 4
    MAX_CELL_SIZE = 20

    def __init__(self, board: BoardState, execution_mode: str, workers: int, on_back, on_start, on_configuration) -> None:
        self.board = board
        self.execution_mode = execution_mode
        self.workers = workers
        self.on_back = on_back
        self.on_start = on_start
        self.on_configuration = on_configuration
        self.show_configuration = True
        self.settings = SimulationSettings(board.rows, board.columns, execution_mode, workers, self._apply_configuration)
        self.cell_size = 8
        self.view_row = max(0, (board.rows - 1) // 2 - 30)
        self.view_column = max(0, (board.columns - 1) // 2 - 45)
        self.canvas = pygame.Rect(54, 171, 810, 510)
        self.buttons: list[Button] = []
        self.notice = ""
        self.notice_seconds = 0.0
        self.dragging = False
        self.paint_alive = True
        self.last_painted_cell: tuple[int, int] | None = None
        self.overview_panel = pygame.Rect(0, 0, 0, 0)
        self.overview_map = pygame.Rect(0, 0, 0, 0)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.settings.handle_event(event):
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.on_back()
                return
            self._handle_keyboard(event)

        if event.type == pygame.MOUSEWHEEL:
            if self.canvas.collidepoint(pygame.mouse.get_pos()):
                self._change_zoom(2 if event.y > 0 else -2)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self._navigate_overview(event.pos):
                return
            if self.canvas.collidepoint(event.pos) and event.button in (1, 3):
                self.dragging = True
                self.paint_alive = (not self._cell_at(event.pos)) if event.button == 1 else False
                self._paint_at(event.pos)
                return
            if event.button == 1:
                for button in self.buttons:
                    if button.handle_event(event):
                        break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 3):
                self.dragging = False
                self.last_painted_cell = None
            if event.button == 1:
                for button in self.buttons:
                    if button.handle_event(event):
                        break

        elif event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.handle_event(event)
            if self.dragging and self.canvas.collidepoint(event.pos):
                self._paint_at(event.pos)

    def update(self, dt: float) -> None:
        self.notice_seconds = max(0.0, self.notice_seconds - dt)

    def draw(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        surface.fill(theme.BG)
        self._draw_header(surface, width)
        if self.show_configuration:
            self.settings.draw(surface)
        self._layout_canvas(width, height)
        self._draw_board(surface)
        self._draw_sidebar(surface, width)
        self._draw_footer(surface, width, height)
        if self.notice_seconds > 0:
            self._draw_notice(surface, width, height)

    def _draw_header(self, surface: pygame.Surface, width: int) -> None:
        theme.draw_text(surface, "Preparar simulación", (54, 30), 26, theme.TEXT, bold=True)
        theme.draw_text(
            surface,
            "Configura el tamaño y el modo; después ajusta las células del tablero.",
            (56, 66),
            13,
            theme.MUTED,
        )

    def _layout_canvas(self, width: int, height: int) -> None:
        sidebar_width = 238
        outer_margin = 54
        gap = 22
        content_top = 222 if self.show_configuration else 122
        content_bottom = height - 96
        self.canvas = pygame.Rect(
            outer_margin,
            content_top,
            max(320, width - outer_margin * 2 - gap - sidebar_width),
            max(300, content_bottom - content_top),
        )

    def _draw_board(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, theme.SURFACE, self.canvas)
        pygame.draw.rect(surface, theme.LINE, self.canvas, width=1)
        inner = self.canvas.inflate(-2, -2)
        pygame.draw.rect(surface, theme.BG, inner)

        columns_visible = max(1, inner.width // self.cell_size)
        rows_visible = max(1, inner.height // self.cell_size)
        self._clamp_view(columns_visible, rows_visible)
        clipped = surface.get_clip()
        surface.set_clip(inner)

        right_col = min(self.board.columns, self.view_column + columns_visible)
        bottom_row = min(self.board.rows, self.view_row + rows_visible)
        for row in range(self.view_row, bottom_row):
            y = inner.y + (row - self.view_row) * self.cell_size
            for column in range(self.view_column, right_col):
                if self.board.is_alive(row, column):
                    x = inner.x + (column - self.view_column) * self.cell_size
                    pygame.draw.rect(
                        surface,
                        theme.LIGHT_GRAY,
                        (x + 1, y + 1, max(1, self.cell_size - 2), max(1, self.cell_size - 2)),
                    )

        grid_color = (42, 42, 42) if self.cell_size >= 6 else (32, 32, 32)
        for x in range(inner.x, inner.x + columns_visible * self.cell_size + 1, self.cell_size):
            pygame.draw.line(surface, grid_color, (x, inner.y), (x, inner.bottom))
        for y in range(inner.y, inner.y + rows_visible * self.cell_size + 1, self.cell_size):
            pygame.draw.line(surface, grid_color, (inner.x, y), (inner.right, y))
        surface.set_clip(clipped)

        self._draw_canvas_toolbar(surface, inner, columns_visible, rows_visible)
        self._draw_overview(surface, inner, columns_visible, rows_visible)

    def _draw_canvas_toolbar(self, surface: pygame.Surface, inner: pygame.Rect, columns_visible: int, rows_visible: int) -> None:
        top_row = self.view_row + 1
        left_column = self.view_column + 1
        bottom_row = min(self.board.rows, self.view_row + rows_visible)
        right_column = min(self.board.columns, self.view_column + columns_visible)
        info = f"Filas {top_row}–{bottom_row} / {self.board.rows}     Columnas {left_column}–{right_column} / {self.board.columns}"
        toolbar = pygame.Rect(inner.left + 1, inner.top + 1, inner.width - 2, 30)
        pygame.draw.rect(surface, theme.SURFACE, toolbar)
        pygame.draw.line(surface, theme.LINE, (toolbar.left, toolbar.bottom), (toolbar.right, toolbar.bottom), 1)
        theme.draw_text(surface, info, (inner.left + 14, inner.top + 12), 11, theme.MUTED, bold=True)
        theme.draw_text(surface, f"Zoom {self.cell_size}px", (inner.right - 14, inner.top + 12), 11, theme.MUTED, anchor="topright")

    def _draw_overview(self, surface: pygame.Surface, inner: pygame.Rect, columns_visible: int, rows_visible: int) -> None:
        """Show the full board and the current viewport at a fixed overview scale."""
        self.overview_panel = pygame.Rect(inner.right - 150, inner.top + 38, 138, 128)
        pygame.draw.rect(surface, theme.SURFACE, self.overview_panel)
        pygame.draw.rect(surface, theme.LINE, self.overview_panel, width=1)
        theme.draw_text(surface, "Vista general", (self.overview_panel.x + 8, self.overview_panel.y + 7), 11, theme.TEXT, bold=True)
        theme.draw_text(
            surface,
            f"{self.board.rows} × {self.board.columns}",
            (self.overview_panel.x + 8, self.overview_panel.y + 23),
            10,
            theme.MUTED,
        )

        max_width, max_height = 112, 82
        scale = min(max_width / self.board.columns, max_height / self.board.rows)
        map_width = max(1, round(self.board.columns * scale))
        map_height = max(1, round(self.board.rows * scale))
        map_x = self.overview_panel.centerx - map_width // 2
        map_y = self.overview_panel.bottom - 10 - map_height
        self.overview_map = pygame.Rect(map_x, map_y, map_width, map_height)
        pygame.draw.rect(surface, theme.BG, self.overview_map)

        # A 36×36 sample keeps the overview cheap to redraw even for million-cell boards.
        sample_rows = min(36, self.board.rows)
        sample_columns = min(36, self.board.columns)
        sample_w = max(1, map_width // sample_columns)
        sample_h = max(1, map_height // sample_rows)
        cells = self.board.cells
        for sample_row in range(sample_rows):
            row = min(self.board.rows - 1, int((sample_row + 0.5) * self.board.rows / sample_rows))
            for sample_column in range(sample_columns):
                column = min(self.board.columns - 1, int((sample_column + 0.5) * self.board.columns / sample_columns))
                if cells[row * self.board.columns + column]:
                    pygame.draw.rect(
                        surface,
                        theme.MID_GRAY,
                        (map_x + sample_column * sample_w, map_y + sample_row * sample_h, sample_w, sample_h),
                    )

        viewport_width = min(map_width, max(1, round(columns_visible * map_width / self.board.columns)))
        viewport_height = min(map_height, max(1, round(rows_visible * map_height / self.board.rows)))
        viewport = pygame.Rect(
            map_x + round(self.view_column * map_width / self.board.columns),
            map_y + round(self.view_row * map_height / self.board.rows),
            viewport_width,
            viewport_height,
        )
        viewport.clamp_ip(self.overview_map)
        pygame.draw.rect(surface, theme.WHITE, viewport, width=2)

    def _navigate_overview(self, position: tuple[int, int]) -> bool:
        if not self.overview_map.collidepoint(position):
            return False
        columns_visible = self._visible_columns()
        rows_visible = self._visible_rows()
        column_fraction = (position[0] - self.overview_map.left) / self.overview_map.width
        row_fraction = (position[1] - self.overview_map.top) / self.overview_map.height
        self.view_column = round(column_fraction * self.board.columns - columns_visible / 2)
        self.view_row = round(row_fraction * self.board.rows - rows_visible / 2)
        self._clamp_view(columns_visible, rows_visible)
        return True

    def _draw_sidebar(self, surface: pygame.Surface, width: int) -> None:
        sidebar = pygame.Rect(width - 292, self.canvas.y, 238, self.canvas.height)
        pygame.draw.rect(surface, theme.SURFACE, sidebar)
        pygame.draw.rect(surface, theme.LINE, sidebar, width=1)
        x = sidebar.x + 18
        theme.draw_text(surface, "Controles", (x, sidebar.y + 18), 16, theme.TEXT, bold=True)
        instructions = (
            "Clic izq.: alternar célula",
            "Arrastrar: pintar",
            "Clic der.: borrar",
            "Rueda: zoom",
            "Minimapa: mover vista",
        )
        for index, instruction in enumerate(instructions):
            theme.draw_text(surface, instruction, (x, sidebar.y + 45 + index * 15), 10, theme.MUTED)

        self.buttons = []
        random_button = Button(
            "Aleatorio · 20%",
            pygame.Rect(x, sidebar.y + 126, sidebar.width - 36, 34),
            self._randomize,
            accent=theme.GRAY,
            hover_accent=theme.LIGHT_GRAY,
        )
        clear_button = Button(
            "Limpiar tablero",
            pygame.Rect(x, sidebar.y + 168, sidebar.width - 36, 34),
            self._clear,
            accent=theme.GRAY,
            hover_accent=theme.LIGHT_GRAY,
        )
        self.buttons.extend((random_button, clear_button))
        random_button.draw(surface)
        clear_button.draw(surface)

        alive_y = sidebar.bottom - 52
        theme.draw_text(surface, f"{self.board.alive_count:,} células vivas".replace(",", "."), (x, alive_y), 12, theme.MUTED, bold=True)

    def _draw_footer(self, surface: pygame.Surface, width: int, height: int) -> None:
        footer_y = height - 66
        back = Button("Volver", pygame.Rect(width - 348, footer_y, 104, 46), self.on_back, accent=theme.GRAY, hover_accent=theme.LIGHT_GRAY)
        start = Button(
            "Iniciar simulación",
            pygame.Rect(width - 228, footer_y, 174, 46),
            self._start,
            primary=True,
            accent=theme.LIGHT_GRAY,
            hover_accent=theme.WHITE,
        )
        self.buttons.extend((back, start))
        back.draw(surface)
        start.draw(surface)

    def _draw_notice(self, surface: pygame.Surface, width: int, height: int) -> None:
        rect = pygame.Rect(width // 2 - 260, height - 128, 520, 42)
        pygame.draw.rect(surface, theme.SURFACE_HOVER, rect)
        theme.draw_text(surface, self.notice, rect.center, 12, theme.TEXT, anchor="center")

    def _handle_keyboard(self, event: pygame.event.Event) -> None:
        step = max(1, self._visible_columns() // 4)
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.view_column -= step
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.view_column += step
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.view_row -= max(1, self._visible_rows() // 4)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.view_row += max(1, self._visible_rows() // 4)
        elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self._change_zoom(2)
        elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self._change_zoom(-2)

    def _cell_at(self, position: tuple[int, int]) -> bool:
        inner = self.canvas.inflate(-2, -2)
        row = self.view_row + (position[1] - inner.y) // self.cell_size
        column = self.view_column + (position[0] - inner.x) // self.cell_size
        if 0 <= row < self.board.rows and 0 <= column < self.board.columns:
            return self.board.is_alive(row, column)
        return False

    def _paint_at(self, position: tuple[int, int]) -> None:
        inner = self.canvas.inflate(-2, -2)
        row = self.view_row + (position[1] - inner.y) // self.cell_size
        column = self.view_column + (position[0] - inner.x) // self.cell_size
        cell = (row, column)
        if cell == self.last_painted_cell:
            return
        self.board.set_alive(row, column, self.paint_alive)
        self.last_painted_cell = cell

    def _visible_columns(self) -> int:
        return max(1, (self.canvas.width - 2) // self.cell_size)

    def _visible_rows(self) -> int:
        return max(1, (self.canvas.height - 2) // self.cell_size)

    def _clamp_view(self, columns_visible: int, rows_visible: int) -> None:
        self.view_column = min(max(0, self.view_column), max(0, self.board.columns - columns_visible))
        self.view_row = min(max(0, self.view_row), max(0, self.board.rows - rows_visible))

    def _change_zoom(self, amount: int) -> None:
        old_columns = self._visible_columns()
        old_rows = self._visible_rows()
        center_column = self.view_column + old_columns // 2
        center_row = self.view_row + old_rows // 2
        self.cell_size = min(self.MAX_CELL_SIZE, max(self.MIN_CELL_SIZE, self.cell_size + amount))
        self.view_column = center_column - self._visible_columns() // 2
        self.view_row = center_row - self._visible_rows() // 2
        self._clamp_view(self._visible_columns(), self._visible_rows())

    def _apply_configuration(self, configuration: dict[str, int | str]) -> None:
        rows = int(configuration["rows"])
        columns = int(configuration["columns"])
        if (rows, columns) != (self.board.rows, self.board.columns):
            self.board = BoardState(rows, columns)
            self.board.load_matrix(inicializar_tablero(rows, columns))
        self.execution_mode = str(configuration["mode"])
        self.workers = int(configuration["workers"])
        self.view_row = max(0, (rows - 1) // 2 - 30)
        self.view_column = max(0, (columns - 1) // 2 - 45)
        self.cell_size = 8
        self.on_configuration(configuration)
        self.notice = "Configuración aplicada. Puedes editar el tablero."
        self.notice_seconds = 2.0

    def _randomize(self) -> None:
        self.board.load_matrix(inicializar_tablero(self.board.rows, self.board.columns))
        self.notice = "Se generó un estado aleatorio con 20% de células vivas."
        self.notice_seconds = 2.0

    def _clear(self) -> None:
        self.board.clear()
        self.notice = "Tablero limpio."
        self.notice_seconds = 2.0

    def _start(self) -> None:
        self.on_start(self.board)
