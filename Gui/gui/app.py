from __future__ import annotations
import pygame
from pygame import _freetype
from . import theme
from .models.board_state import BoardState
from .screens.board_preparation import BoardPreparation
from .screens.main_menu import MainMenu
from .screens.simulation import SimulationScreen
from src.logic import inicializar_tablero


class ConwayApp:
    def __init__(self) -> None:
        pygame.init()
        _freetype.init()
        pygame.display.set_caption("Conway · Vida en Paralelo")
        self.screen = pygame.display.set_mode(theme.WINDOW_SIZE, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.menu = MainMenu(self.stop, self.show_settings)
        self.active_screen = self.menu
        self.configuration: dict[str, int | str] | None = None
        self.board_state: BoardState | None = None
        self.initial_state: BoardState | None = None
        self.preparation: BoardPreparation | None = None
        self.simulation: SimulationScreen | None = None

    def run(self) -> None:
        try:
            while self.running:
                dt = self.clock.tick(theme.FPS) / 1000.0
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.stop()
                    elif event.type == pygame.VIDEORESIZE:
                        self.screen = pygame.display.get_surface() or self.screen
                    else:
                        self.active_screen.handle_event(event)

                self.active_screen.update(dt)
                self.active_screen.draw(self.screen)
                pygame.display.flip()
        except KeyboardInterrupt:
            self.stop()
        finally:
            pygame.quit()

    def show_settings(self) -> None:
        self.configuration = {"rows": 100, "columns": 100, "mode": "sequential", "workers": 2}
        self.board_state = BoardState(100, 100)
        self.board_state.load_matrix(inicializar_tablero(100, 100))
        self.preparation = BoardPreparation(
            self.board_state,
            "sequential",
            2,
            self.show_menu,
            self.save_initial_state,
            self.save_configuration,
        )
        self.active_screen = self.preparation

    def show_menu(self) -> None:
        self.active_screen = self.menu

    def show_preparation(self) -> None:
        self.active_screen = self.preparation or self.menu

    def save_configuration(self, configuration: dict[str, int | str]) -> None:
        self.configuration = configuration
        if self.preparation is not None:
            self.board_state = self.preparation.board

    def save_initial_state(self, board: BoardState) -> None:
        self.initial_state = board.copy()
        if self.configuration is None:
            return
        self.simulation = SimulationScreen(
            self.initial_state,
            str(self.configuration["mode"]),
            int(self.configuration["workers"]),
            self.show_preparation,
        )
        self.active_screen = self.simulation

    def stop(self) -> None:
        self.running = False
        close = getattr(self.active_screen, "close", None)
        if close is not None:
            close()
