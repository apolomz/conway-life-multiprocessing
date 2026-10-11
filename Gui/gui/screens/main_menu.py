"""Simple main menu for the Conway Life application."""

from __future__ import annotations

import pygame

from .. import theme
from ..components import Button


class MainMenu:
    def __init__(self, on_quit, on_new_simulation) -> None:
        self.on_quit = on_quit
        self.on_new_simulation = on_new_simulation
        self.show_help = False
        self.notice = ""
        self.notice_seconds = 0.0
        self.buttons: list[Button] = []

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.show_help:
                self.show_help = False
            return
        if self.show_help:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.show_help = False
            return
        for button in self.buttons:
            if button.handle_event(event):
                break

    def update(self, dt: float) -> None:
        self.notice_seconds = max(0.0, self.notice_seconds - dt)

    def draw(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        surface.fill(theme.BG)
        center_x = width // 2
        theme.draw_text(
            surface,
            "Juego de la vida de Conway",
            (center_x, max(72, height // 5)),
            34,
            theme.TEXT,
            bold=True,
            anchor="midtop",
        )
        theme.draw_text(
            surface,
            "Simulación secuencial y paralela",
            (center_x, max(120, height // 5 + 48)),
            18,
            theme.MUTED,
            anchor="midtop",
        )
        self._draw_controls(surface, center_x, height // 2)
        if self.notice_seconds > 0:
            theme.draw_text(surface, self.notice, (center_x, height - 40), 13, theme.MUTED, anchor="midtop")
        if self.show_help:
            self._draw_help(surface)

    def _draw_controls(self, surface: pygame.Surface, center_x: int, y: int) -> None:
        button_width = 220
        button_height = 44
        gap = 12
        total_height = button_height * 3 + gap * 2
        x = center_x - button_width // 2
        first_y = y - total_height // 2
        self.buttons = [
            Button("Nueva simulación", pygame.Rect(x, first_y, button_width, button_height), self.on_new_simulation, primary=True, accent=theme.LIGHT_GRAY, hover_accent=theme.WHITE),
            Button("Cómo funciona", pygame.Rect(x, first_y + button_height + gap, button_width, button_height), self._open_help),
            Button("Salir", pygame.Rect(x, first_y + 2 * (button_height + gap), button_width, button_height), self.on_quit),
        ]
        for button in self.buttons:
            button.draw(surface)

    def _draw_help(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        rect = pygame.Rect(width // 2 - 250, height // 2 - 120, 500, 240)
        pygame.draw.rect(surface, theme.SURFACE, rect)
        pygame.draw.rect(surface, theme.LINE, rect, width=1)
        theme.draw_text(surface, "Cómo funciona", (rect.x + 22, rect.y + 18), 22, theme.TEXT, bold=True)
        lines = (
            "Cada célula observa sus ocho vecinas.",
            "Sobrevive con dos o tres vecinas vivas.",
            "Nace una célula cuando tiene tres vecinas.",
            "En los demás casos, muere o permanece vacía.",
        )
        for index, line in enumerate(lines):
            theme.draw_text(surface, line, (rect.x + 22, rect.y + 62 + index * 30), 14, theme.MUTED)
        theme.draw_text(surface, "Pulsa Esc o haz clic para volver", (rect.x + 22, rect.bottom - 30), 12, theme.MUTED)

    def _open_help(self) -> None:
        self.show_help = True
