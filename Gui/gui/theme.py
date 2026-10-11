from __future__ import annotations

import pygame
from pygame import _freetype
from functools import lru_cache


WINDOW_SIZE = (1180, 760)
FPS = 60

BG = (12, 12, 12)
SURFACE = (24, 24, 24)
SURFACE_HOVER = (40, 40, 40)
LINE = (78, 78, 78)
TEXT = (242, 242, 242)
MUTED = (170, 170, 170)

WHITE = (250, 250, 250)
LIGHT_GRAY = (218, 218, 218)
MID_GRAY = (160, 160, 160)
GRAY = (112, 112, 112)
DARK_GRAY = (76, 76, 76)


@lru_cache(maxsize=24)
def font(size: int, *, bold: bool = False) -> _freetype.Font:
    """Return a cached FreeType font, bypassing pygame.font's sysfont import."""
    result = _freetype.Font(None, size)
    result.strong = bold
    return result


def draw_text(
    surface: pygame.Surface,
    text: str,
    position: tuple[int, int],
    size: int,
    color: tuple[int, int, int] = TEXT,
    *,
    bold: bool = False,
    anchor: str = "topleft",
) -> pygame.Rect:
    rendered, _ = font(size, bold=bold).render(text, fgcolor=color)
    rect = rendered.get_rect()
    setattr(rect, anchor, position)
    surface.blit(rendered, rect)
    return rect
