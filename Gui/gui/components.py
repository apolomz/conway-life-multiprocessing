from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import pygame
from . import theme


@dataclass
class Button:
    label: str
    rect: pygame.Rect
    on_click: Callable[[], None]
    primary: bool = False
    accent: tuple[int, int, int] = theme.LIGHT_GRAY
    hover_accent: tuple[int, int, int] = theme.WHITE
    hover: bool = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()
                return True
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.hover:
                self.on_click()
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        if self.primary:
            fill = self.hover_accent if self.hover else self.accent
            foreground = theme.BG
            pygame.draw.rect(surface, fill, self.rect)
        else:
            fill = theme.SURFACE_HOVER if self.hover else theme.SURFACE
            foreground = theme.TEXT
            pygame.draw.rect(surface, fill, self.rect)
            border = self.hover_accent if self.hover else self.accent
            pygame.draw.rect(surface, border, self.rect, width=1)

        theme.draw_text(surface, self.label, self.rect.center, 15, foreground, bold=self.primary, anchor="center")
