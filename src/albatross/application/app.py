"""Game application: event handling, fixed-step loop and wiring."""

from __future__ import annotations

import contextlib
from collections.abc import Sequence
from typing import Protocol

import pygame

from albatross.application.timing import FixedStepClock
from albatross.domain.config import DEFAULT_FLIGHT_CONFIG
from albatross.domain.session import GamePhase, GameSession, SessionState
from albatross.infrastructure.records import RecordStore
from albatross.presentation import theme
from albatross.presentation.audio import SoundEngine
from albatross.presentation.i18n import Translator
from albatross.presentation.renderer import Renderer


class Clock(Protocol):
    def tick(self, framerate: int = 0) -> int: ...


class GameApp:
    """One game process.

    ``tick`` is deliberately independent of the real clock, which makes the
    whole loop testable with dummy SDL drivers and synthetic events.
    """

    def __init__(
        self,
        *,
        session: GameSession,
        renderer: Renderer,
        sound: SoundEngine,
        store: RecordStore,
        screen: pygame.Surface,
        translator: Translator | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._session = session
        self._renderer = renderer
        self._sound = sound
        self._store = store
        self._screen = screen
        self._translator = translator if translator is not None else Translator()
        self._clock: Clock = clock if clock is not None else pygame.time.Clock()
        self._fixed = FixedStepClock(
            step_s=session.config.step_s,
            max_frame_s=session.config.max_frame_s,
        )
        self._running = True

    @classmethod
    def create(cls) -> GameApp:
        """Build the real application with a window, audio and stored record."""
        pygame.mixer.pre_init(44_100, -16, 2)
        pygame.init()
        pygame.display.set_caption("Albatross")
        screen = pygame.display.set_mode((theme.WINDOW_WIDTH, theme.WINDOW_HEIGHT))

        config = DEFAULT_FLIGHT_CONFIG
        store = RecordStore()
        session = GameSession(config, best_distance_m=store.load_best())
        sound = SoundEngine()
        sound.start()
        return cls(
            session=session,
            renderer=Renderer((theme.WINDOW_WIDTH, theme.WINDOW_HEIGHT), config),
            sound=sound,
            store=store,
            screen=screen,
        )

    def run(self) -> None:
        """Run the interactive loop until the window closes."""
        try:
            while self._running:
                frame_s = self._clock.tick(theme.FPS) / 1000.0
                self.tick(pygame.event.get(), frame_s)
                pygame.display.flip()
        finally:
            pygame.quit()

    def tick(self, events: Sequence[pygame.event.Event], frame_s: float) -> bool:
        """Process one frame. Returns ``False`` after a quit request."""
        self._handle_events(events)
        if not self._running:
            return False

        clamped_s = min(max(0.0, frame_s), self._session.config.max_frame_s)
        steps = self._fixed.feed(clamped_s)
        for _ in range(steps):
            if self._session.state.phase is not GamePhase.PLAYING:
                break
            self._session.advance(self._session.config.step_s)
            fresh_state = self._session.state
            if fresh_state.phase is GamePhase.GAME_OVER:
                self._persist_record()
                break

        frame = self._renderer.render(
            self._session.state,
            clamped_s,
            self._translator,
            self._sound.muted,
        )
        self._screen.blit(frame, (0, 0))
        return True

    @property
    def session(self) -> GameSession:
        return self._session

    @property
    def translator(self) -> Translator:
        return self._translator

    @property
    def sound(self) -> SoundEngine:
        return self._sound

    def _handle_events(self, events: Sequence[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self._running = False
                return
            if event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._primary_action()

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self._session.toggle_pause()
        elif key == pygame.K_SPACE:
            self._primary_action()
        elif key == pygame.K_r:
            if self._session.state.phase is GamePhase.GAME_OVER:
                self._session.restart()
        elif key == pygame.K_l:
            self._translator.toggle()
        elif key == pygame.K_m:
            self._sound.toggle_mute()

    def _primary_action(self) -> None:
        state = self._session.state
        if state.phase is GamePhase.MENU:
            self._session.start()
        elif state.phase is GamePhase.PLAYING:
            if self._session.request_flap():
                self._sound.on_flap()
                self._renderer.notify_flap()
        elif state.phase is GamePhase.GAME_OVER:
            self._session.restart()

    def _persist_record(self) -> None:
        state: SessionState = self._session.state
        if state.best_distance_m is None:
            return
        with contextlib.suppress(OSError):
            self._store.save_best(state.best_distance_m)
