"""Simple chart registry and rendering utilities."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Deque, List, Tuple

import pygame

ChartCallback = Callable[[], float]


@dataclass
class Chart:
    name: str
    value_name: str
    callback: ChartCallback
    history: Deque[Tuple[float, float]] = field(default_factory=lambda: deque(maxlen=300))

    def sample(self, timestamp: float) -> None:
        try:
            value = float(self.callback())
        except Exception:
            # On callback failure, skip this sample but keep the chart alive.
            return
        self.history.append((timestamp, value))

    def _value_range(self) -> Tuple[float, float]:
        values = [v for _, v in self.history]
        if not values:
            return (0.0, 1.0)
        v_min = min(values)
        v_max = max(values)
        if abs(v_max - v_min) < 1e-9:
            padding = max(1.0, abs(v_max) * 0.1 + 1.0)
            return (v_min - padding, v_max + padding)
        return (v_min, v_max)

    def render(self, surface: pygame.Surface, rect: pygame.Rect, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, (25, 25, 25), rect)
        pygame.draw.rect(surface, (80, 80, 80), rect, 1)

        title = font.render(self.name, True, (220, 220, 220))
        surface.blit(title, (rect.x + 8, rect.y + 4))

        label = font.render(self.value_name, True, (180, 180, 180))
        surface.blit(label, (rect.x + 8, rect.y + 20))

        if len(self.history) < 2:
            return

        times = [t for t, _ in self.history]
        start = times[0]
        duration = max(times[-1] - start, 1.0)
        v_min, v_max = self._value_range()
        scale = max(v_max - v_min, 1e-6)

        padding_top = 28
        padding_bottom = 12
        padding_side = 8
        usable_width = max(1, rect.width - padding_side * 2)
        usable_height = max(1, rect.height - padding_top - padding_bottom)

        points: List[Tuple[int, int]] = []
        for timestamp, value in self.history:
            x = rect.x + padding_side + int(((timestamp - start) / duration) * usable_width)
            normalized = (value - v_min) / scale
            y = rect.y + rect.height - padding_bottom - int(normalized * usable_height)
            points.append((x, y))

        if len(points) >= 2:
            pygame.draw.lines(surface, (120, 200, 255), False, points, 2)

        latest_value = self.history[-1][1]
        latest_text = font.render(f"{latest_value:.1f}", True, (255, 255, 255))
        surface.blit(latest_text, (rect.right - latest_text.get_width() - 8, rect.y + 4))


class ChartManager:
    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self._accumulator = 0.0
        self._charts: List[Chart] = []
        self._font: pygame.font.Font | None = None
        self._scroll_x = 0.0
        self._scroll_speed = 40.0
        self._view_columns = 2.5
        self._last_sample_time: float | None = None

    def register_chart(self, name: str, value_name: str, callback: ChartCallback) -> Chart:
        chart = Chart(name=name, value_name=value_name, callback=callback)
        self._charts.append(chart)
        return chart

    def update(self, dt: float) -> None:
        self._accumulator += dt
        while self._accumulator >= self.sample_interval:
            self._accumulator -= self.sample_interval
            self._poll()

    def _poll(self) -> None:
        timestamp = time.time()
        self._last_sample_time = timestamp
        for chart in self._charts:
            chart.sample(timestamp)

    def render(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        if not self._charts:
            pygame.draw.rect(surface, (30, 30, 30), rect)
            pygame.draw.rect(surface, (80, 80, 80), rect, 1)
            return

        chart_height = rect.height
        chart_width = rect.width / max(self._view_columns, 0.1)
        chart_w = max(1, int(chart_width))
        total_width = chart_width * len(self._charts)

        max_scroll = max(0.0, total_width - rect.width)
        self._scroll_x = max(0.0, min(self._scroll_x, max_scroll))

        font = self._font or pygame.font.Font(None, 20)
        self._font = font

        pygame.draw.rect(surface, (20, 20, 20), rect)
        pygame.draw.rect(surface, (50, 50, 50), rect, 1)

        clip = surface.get_clip()
        surface.set_clip(rect)

        origin_x = rect.x - self._scroll_x
        for i, chart in enumerate(self._charts):
            chart_rect = pygame.Rect(
                int(origin_x + i * chart_width),
                rect.y,
                chart_w,
                chart_height,
            )
            if chart_rect.right < rect.x or chart_rect.x > rect.right:
                continue
            chart.render(surface, chart_rect, font)

        surface.set_clip(clip)

    def scroll(self, dy: float) -> None:
        self._scroll_x = max(0.0, self._scroll_x + dy * self._scroll_speed)


_MANAGER = ChartManager()


def register_chart(name: str, value_name: str, callback: ChartCallback) -> Chart:
    """Registers a chart to be sampled and rendered."""
    return _MANAGER.register_chart(name, value_name, callback)

def update(dt: float) -> None:
    """Advances the polling timer."""
    _MANAGER.update(dt)

def render(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Renders all registered charts inside the given rect."""
    _MANAGER.render(surface, rect)

def scroll(dy: float) -> None:
    """Scrolls the chart viewport horizontally (dy is mouse wheel delta)."""
    _MANAGER.scroll(dy)

def first_sample_age() -> float:
    """Returns seconds since the oldest datapoint across charts was sampled."""
    oldest = None
    for chart in _MANAGER._charts:
        if chart.history:
            timestamp = chart.history[0][0]
            if oldest is None or timestamp < oldest:
                oldest = timestamp
    if oldest is None:
        return 0.0
    return max(0.0, time.time() - oldest)
