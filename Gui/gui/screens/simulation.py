from __future__ import annotations
from concurrent.futures import Future, ThreadPoolExecutor
import pygame
from .. import theme
from ..components import Button
from ..models.board_state import BoardState
from ..simulation_engine import SimulationEngine
from .board_preparation import BoardPreparation


class SimulationScreen(BoardPreparation):
    """Reuse the board viewport while rendering simulation controls and state."""

    MIN_SPEED = 1
    MAX_SPEED = 30

    def __init__(self, initial_state: BoardState, execution_mode: str, workers: int, on_back) -> None:
        self.initial_state = initial_state.copy()
        super().__init__(initial_state.copy(), execution_mode, workers, on_back, lambda _board: None, lambda _configuration: None)
        self.show_configuration = False
        self.engine = SimulationEngine()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="conway-generation")
        self.future: Future[BoardState] | None = None
        self.future_epoch = 0
        self.epoch = 0
        self.generation = 0
        self.generations_per_second = 6
        self.elapsed = 0.0
        self.running = True
        self.closed = False
        self.error = ""

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._navigate_overview(event.pos):
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._go_back()
                return
            if event.key == pygame.K_SPACE:
                self._toggle_running()
                return
            self._handle_keyboard(event)

        if event.type == pygame.MOUSEWHEEL:
            if self.canvas.collidepoint(pygame.mouse.get_pos()):
                self._change_zoom(2 if event.y > 0 else -2)
            return

        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.handle_event(event)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for button in self.buttons:
                if button.handle_event(event):
                    break

    def update(self, dt: float) -> None:
        if self.future is not None and self.future.done():
            completed_future = self.future
            completed_epoch = self.future_epoch
            self.future = None
            try:
                result = completed_future.result()
            except Exception as error:
                if completed_epoch == self.epoch:
                    self.running = False
                    self.error = str(error)
            else:
                if completed_epoch == self.epoch:
                    self.board = result
                    self.generation += 1

        if self.running and self.future is None:
            self.elapsed += dt
            if self.elapsed >= 1 / self.generations_per_second:
                self.elapsed = 0.0
                self._schedule_generation()

    def _draw_header(self, surface: pygame.Surface, width: int) -> None:
        theme.draw_text(surface, "Simulación", (54, 42), 28, theme.TEXT, bold=True)
        mode = "Secuencial" if self.execution_mode == "sequential" else f"Paralelo · {self.workers} hilos"
        theme.draw_text(surface, f"{self.board.rows} × {self.board.columns}  ·  {mode}", (56, 82), 13, theme.MUTED)

    def _draw_sidebar(self, surface: pygame.Surface, width: int) -> None:
        sidebar = pygame.Rect(width - 292, self.canvas.y, 238, self.canvas.height)
        pygame.draw.rect(surface, theme.SURFACE, sidebar)
        pygame.draw.rect(surface, theme.LINE, sidebar, width=1)
        x = sidebar.x + 18
        theme.draw_text(surface, "Controles", (x, sidebar.y + 18), 16, theme.TEXT, bold=True)
        state_label = "Calculando…" if self.future is not None else ("En ejecución" if self.running else "En pausa")
        theme.draw_text(surface, state_label, (x, sidebar.y + 44), 11, theme.MUTED)

        play_label = "Pausar" if self.running else "Continuar"
        play = Button(play_label, pygame.Rect(x, sidebar.y + 76, sidebar.width - 36, 38), self._toggle_running, primary=True, accent=theme.LIGHT_GRAY, hover_accent=theme.WHITE)
        step = Button("Avanzar un paso", pygame.Rect(x, sidebar.y + 122, sidebar.width - 36, 36), self._step_once, accent=theme.GRAY, hover_accent=theme.LIGHT_GRAY)
        restart = Button("Reiniciar", pygame.Rect(x, sidebar.y + 166, sidebar.width - 36, 36), self._restart, accent=theme.GRAY, hover_accent=theme.LIGHT_GRAY)
        self.buttons = [play, step, restart]
        for button in self.buttons:
            button.draw(surface)

        divider_y = sidebar.y + 220
        pygame.draw.line(surface, theme.LINE, (x, divider_y), (sidebar.right - 18, divider_y), 1)
        theme.draw_text(surface, "Velocidad", (x, divider_y + 16), 13, theme.TEXT, bold=True)
        theme.draw_text(surface, "Generaciones por segundo", (x, divider_y + 38), 10, theme.MUTED)
        self._draw_speed_control(surface, x, divider_y + 62, sidebar.right - 18)

        stats_y = divider_y + 124
        theme.draw_text(surface, f"Generación  {self.generation:,}".replace(",", "."), (x, stats_y), 12, theme.TEXT, bold=True)
        theme.draw_text(surface, f"Células vivas  {self.board.alive_count:,}".replace(",", "."), (x, stats_y + 25), 11, theme.MUTED)
        if self.error:
            theme.draw_text(surface, "Error del motor", (x, stats_y + 55), 11, theme.MUTED, bold=True)

        shortcuts_y = stats_y + 82
        pygame.draw.line(surface, theme.LINE, (x, shortcuts_y - 12), (sidebar.right - 18, shortcuts_y - 12), 1)
        theme.draw_text(surface, "Atajos", (x, shortcuts_y), 13, theme.TEXT, bold=True)
        shortcuts = (
            "Espacio: pausar / continuar",
            "Rueda: zoom",
            "Flechas o WASD: mover vista",
            "Minimapa: mover vista",
        )
        for index, shortcut in enumerate(shortcuts):
            theme.draw_text(surface, shortcut, (x, shortcuts_y + 22 + index * 17), 10, theme.MUTED)

    def _draw_speed_control(self, surface: pygame.Surface, x: int, y: int, right: int) -> None:
        minus = Button("−", pygame.Rect(x, y, 38, 34), self._decrease_speed, accent=theme.GRAY, hover_accent=theme.LIGHT_GRAY)
        plus = Button("+", pygame.Rect(right - 38, y, 38, 34), self._increase_speed, accent=theme.GRAY, hover_accent=theme.LIGHT_GRAY)
        value_rect = pygame.Rect(x + 46, y, max(60, right - x - 92), 34)
        pygame.draw.rect(surface, theme.SURFACE, value_rect)
        pygame.draw.rect(surface, theme.LINE, value_rect, width=1)
        theme.draw_text(surface, str(self.generations_per_second), value_rect.center, 14, theme.TEXT, bold=True, anchor="center")
        minus.draw(surface)
        plus.draw(surface)
        self.buttons.extend((minus, plus))

    def _draw_footer(self, surface: pygame.Surface, width: int, height: int) -> None:
        footer_y = height - 66
        back = Button("Volver a preparación", pygame.Rect(width - 234, footer_y, 180, 46), self._go_back, accent=theme.GRAY, hover_accent=theme.LIGHT_GRAY)
        self.buttons.append(back)
        back.draw(surface)
        if self.error:
            theme.draw_text(surface, f"Error del motor: {self.error[:72]}", (54, footer_y - 14), 11, theme.MUTED)

    def _schedule_generation(self) -> None:
        if self.future is None:
            self.future_epoch = self.epoch
            self.future = self.executor.submit(
                self.engine.next_generation,
                self.board.copy(),
                self.execution_mode,
                self.workers,
            )

    def _step_once(self) -> None:
        self.running = False
        self.elapsed = 0.0
        self._schedule_generation()

    def _toggle_running(self) -> None:
        self.error = ""
        self.running = not self.running

    def _restart(self) -> None:
        self.epoch += 1
        self.running = False
        self.elapsed = 0.0
        self.generation = 0
        self.error = ""
        self.board = self.initial_state.copy()
        self.view_row = max(0, (self.board.rows - 1) // 2 - self._visible_rows() // 2)
        self.view_column = max(0, (self.board.columns - 1) // 2 - self._visible_columns() // 2)
        self._clamp_view(self._visible_columns(), self._visible_rows())

    def _increase_speed(self) -> None:
        self.generations_per_second = min(self.MAX_SPEED, self.generations_per_second + 1)

    def _decrease_speed(self) -> None:
        self.generations_per_second = max(self.MIN_SPEED, self.generations_per_second - 1)

    def _go_back(self) -> None:
        self.running = False
        self.epoch += 1
        self.close()
        self.on_back()

    def close(self) -> None:
        if not self.closed:
            self.closed = True
            self.executor.shutdown(wait=False, cancel_futures=True)
