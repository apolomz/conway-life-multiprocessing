"""Compact simulation settings panel embedded in the board preparation screen."""

from __future__ import annotations

import os

import pygame

from .. import theme
from ..components import Button


class SimulationSettings:
    PRESETS = ((100, 100), (500, 500), (1000, 1000))
    MIN_DIMENSION = 10
    MAX_DIMENSION = 1000

    def __init__(self, rows: int, columns: int, mode: str, workers: int, on_apply) -> None:
        self.on_apply = on_apply
        self.rows = str(rows)
        self.columns = str(columns)
        self.execution_mode = mode
        self.workers = workers
        self.focused_field: str | None = None
        self.replace_field_on_input = False
        self.error_message = ""
        self.buttons: list[Button] = []
        self.field_rects: dict[str, pygame.Rect] = {}

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused_field = next(
                (name for name, rect in self.field_rects.items() if rect.collidepoint(event.pos)),
                None,
            )
            self.replace_field_on_input = self.focused_field is not None
            return self.focused_field is not None

        if event.type == pygame.KEYDOWN and self.focused_field:
            self._handle_text_input(event)
            return True

        handled = False
        for button in self.buttons:
            if button.handle_event(event):
                handled = True
                break
        return handled

    def draw(self, surface: pygame.Surface) -> None:
        width, _ = surface.get_size()
        panel = pygame.Rect(54, 96, width - 108, 112)
        pygame.draw.rect(surface, theme.SURFACE, panel)
        pygame.draw.rect(surface, theme.LINE, panel, width=1)
        theme.draw_text(surface, "Configuración", (panel.x + 14, panel.y + 9), 14, theme.TEXT, bold=True)

        y = panel.y + 46
        label_y = y - 17
        start_x = panel.x + 14
        self.field_rects = {
            "rows": pygame.Rect(start_x, y, 72, 34),
            "columns": pygame.Rect(start_x + 82, y, 72, 34),
        }
        self._draw_number_field(surface, "Filas", "rows", self.rows)
        self._draw_number_field(surface, "Columnas", "columns", self.columns)

        self.buttons = []
        preset_x = start_x + 166
        preset_widths = (78, 78, 88)
        for index, ((rows, columns), preset_width) in enumerate(zip(self.PRESETS, preset_widths)):
            button = Button(
                f"{rows}×{columns}",
                pygame.Rect(preset_x, y, preset_width, 34),
                lambda r=rows, c=columns: self._set_preset(r, c),
                primary=(int(self.rows or 0), int(self.columns or 0)) == (rows, columns),
                accent=theme.MID_GRAY,
                hover_accent=theme.LIGHT_GRAY,
            )
            self.buttons.append(button)
            preset_x += preset_width + 5

        mode_x = preset_x + 16
        mode_width = 104
        for index, (label, mode) in enumerate((("Secuencial", "sequential"), ("Paralelo", "parallel"))):
            button = Button(
                label,
                pygame.Rect(mode_x + index * (mode_width + 6), y, mode_width, 34),
                lambda selected=mode: self._set_mode(selected),
                primary=self.execution_mode == mode,
                accent=theme.MID_GRAY,
                hover_accent=theme.LIGHT_GRAY,
            )
            self.buttons.append(button)

        worker_x = mode_x + mode_width * 2 + 34
        theme.draw_text(surface, "Hilos", (worker_x, label_y), 11, theme.MUTED, bold=True)
        self._draw_stepper(surface, worker_x, y, worker_x + 118)
        apply_width = 144
        apply_rect = pygame.Rect(panel.right - apply_width - 14, y, apply_width, 34)
        self.buttons.append(
            Button("Aplicar", apply_rect, self._submit, primary=True, accent=theme.LIGHT_GRAY, hover_accent=theme.WHITE)
        )

        for button in self.buttons:
            button.draw(surface)
        if self.execution_mode != "parallel":
            theme.draw_text(surface, "Hilos: solo para modo paralelo", (worker_x, y + 39), 10, theme.MUTED)
        if self.error_message:
            theme.draw_text(surface, self.error_message, (start_x, panel.bottom - 18), 11, theme.LIGHT_GRAY)

    def _draw_number_field(self, surface: pygame.Surface, label: str, name: str, value: str) -> None:
        rect = self.field_rects[name]
        theme.draw_text(surface, label, (rect.x, rect.y - 17), 11, theme.MUTED, bold=True)
        pygame.draw.rect(surface, theme.BG, rect)
        outline = theme.LIGHT_GRAY if self.focused_field == name else theme.LINE
        pygame.draw.rect(surface, outline, rect, width=1)
        theme.draw_text(surface, value or "0", (rect.x + 8, rect.centery), 14, theme.TEXT, anchor="midleft")

    def _draw_stepper(self, surface: pygame.Surface, x: int, y: int, right: int) -> None:
        button_width = 30
        minus = Button("−", pygame.Rect(x, y, button_width, 34), self._decrease_workers)
        plus = Button("+", pygame.Rect(right - button_width, y, button_width, 34), self._increase_workers)
        value_rect = pygame.Rect(x + button_width + 5, y, right - x - 2 * button_width - 10, 34)
        pygame.draw.rect(surface, theme.BG, value_rect)
        pygame.draw.rect(surface, theme.LINE, value_rect, width=1)
        theme.draw_text(surface, str(self.workers), value_rect.center, 13, theme.TEXT, anchor="center")
        self.buttons.extend((minus, plus))

    def _handle_text_input(self, event: pygame.event.Event) -> None:
        if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.focused_field = None
        elif event.key == pygame.K_BACKSPACE:
            value = "" if self.replace_field_on_input else self._field_value(self.focused_field)[:-1]
            self._set_field_value(self.focused_field, value)
            self.replace_field_on_input = False
        elif event.unicode.isdigit():
            current = "" if self.replace_field_on_input else self._field_value(self.focused_field)
            if len(current) < 4:
                self._set_field_value(self.focused_field, current + event.unicode)
            self.replace_field_on_input = False
        self.error_message = ""

    def _field_value(self, name: str | None) -> str:
        return self.rows if name == "rows" else self.columns

    def _set_field_value(self, name: str | None, value: str) -> None:
        if name == "rows":
            self.rows = value
        elif name == "columns":
            self.columns = value

    def _set_preset(self, rows: int, columns: int) -> None:
        self.rows, self.columns = str(rows), str(columns)
        self.focused_field = None

    def _set_mode(self, mode: str) -> None:
        self.execution_mode = mode

    def _decrease_workers(self) -> None:
        self.workers = max(2, self.workers - 1)

    def _increase_workers(self) -> None:
        self.workers = min(os.cpu_count() or 2, self.workers + 1)

    def _submit(self) -> None:
        try:
            rows, columns = int(self.rows), int(self.columns)
        except ValueError:
            self.error_message = "Ingresa filas y columnas válidas."
            return
        if not (self.MIN_DIMENSION <= rows <= self.MAX_DIMENSION and self.MIN_DIMENSION <= columns <= self.MAX_DIMENSION):
            self.error_message = "Cada dimensión debe estar entre 10 y 1000."
            return

        self.on_apply({
            "rows": rows,
            "columns": columns,
            "mode": self.execution_mode,
            "workers": self.workers if self.execution_mode == "parallel" else 1,
        })
        self.error_message = ""
