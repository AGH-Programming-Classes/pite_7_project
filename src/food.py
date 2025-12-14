"""Module defining food items and their sources for the simulation."""

from abc import ABC, abstractmethod
import pygame


class Food:
    """Represents a single piece of food that an agent can consume."""

    def __init__(self, position: tuple, value: int, food_type: str, expiry_time: int):
        self.x, self.y = position  # Grid position (x, y)
        self.value = value        # Energy provided
        self.type = food_type     # 'herbivore' or 'carnivore'
        self.expiry_time = expiry_time
        self.age = 0              # Age (in ticks)

    def update(self) -> bool:
        """Ages the item. Returns True if the food has expired."""
        self.age += 1
        return self.age >= self.expiry_time

    def render(self, window, cell_size: int, panel_x: int, panel_y: int):
        """Renders the food item on the screen."""
        # Color based on type
        color = (0, 200, 0) if self.type == 'herbivore' else (200, 0, 0)

        center_x = panel_x + self.x * cell_size + cell_size // 2
        center_y = panel_y + self.y * cell_size + cell_size // 2

        pygame.draw.circle(window, color, (center_x, center_y), cell_size // 6)

class FoodSource(ABC):
    """Abstract base class for all food sources (producers)."""

    def __init__(self, position: tuple, area_id: int):
        self.x, self.y = position
        self.area_id = area_id
        self.food_left = 0
        self.is_destroyed = False

    @abstractmethod
    def update(self) -> Food | None:
        """Implements growth, production, and potential destruction logic.
        Returns a new Food object if one is dropped, otherwise None."""


    @abstractmethod
    def render(self, window, cell_size: int, food_items: list, panel_offset: tuple):
        """Renders the food source."""


    def destroy(self):
        """Marks the source as destroyed."""
        self.is_destroyed = True

# Example
class SimpleGrassPatch(FoodSource):
    """A simple herbivore food source that regenerates and periodically drops food."""

    FONT = None

    def __init__(self, position: tuple, area_id: int):
        super().__init__(position, area_id)
        self.food_left = 100 # Initial capacity
        self.max_capacity = 100
        self.production_interval = 100 # Drops food every 100 ticks
        self.tick_count = 0

    @classmethod
    def get_font(cls):
        """Return a shared pygame Font instance"""
        if cls.FONT is None:
            cls.FONT = pygame.font.Font(None, 14)
        return cls.FONT

    def update(self) -> Food | None:
        """Regenerates the source and occasionally drops a Food object."""
        if self.is_destroyed:
            return None

        if self.food_left < self.max_capacity:
            self.food_left = min(self.max_capacity, self.food_left + 0.1)

        self.tick_count += 1
        if self.tick_count >= self.production_interval and self.food_left >= 10:
            self.tick_count = 0
            self.food_left -= 10

            spawn_pos = (self.x, self.y)

            return Food(
                spawn_pos,
                value=20,
                food_type='herbivore',
                expiry_time=500
            )

        return None

    def render(self, window, cell_size: int, food_items: list, panel_offset: tuple):
        """Renders the grass patch (source) and displays the count of active food items."""

        panel_x, panel_y = panel_offset
        rect = pygame.Rect(panel_x + self.x * cell_size
                           , panel_y + self.y * cell_size,
                           cell_size,
                           cell_size
                        )
        capacity_ratio = self.food_left / self.max_capacity
        r = 50 + int(50 * capacity_ratio)
        g = 150 + int(100 * capacity_ratio)
        b = 50 + int(50 * capacity_ratio)
        pygame.draw.rect(window, (r, g, b), rect)

        food_count = sum(
            1 for food in food_items
            if food.x == self.x and food.y == self.y
        )

        if food_count > 0:
            food_count_surface = self.get_font().render(
                f"{food_count}",
                True,
                (0, 200, 0)
            )

            text_rect = food_count_surface.get_rect(
                topleft=(
                    panel_x + self.x * cell_size + cell_size * 0.75,
                    panel_y + self.y * cell_size + cell_size * 0.5
                )
)

            window.blit(food_count_surface, text_rect)
