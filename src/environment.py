"""Environment module containing the main simulation state."""

import threading
import time
import pygame
from food import SimpleGrassPatch


class Environment:
    """
    This is a de-facto container for global application state and
    has a "public" function called by the application game loop: render

    This should also expose all things that the user could do (like a button hit)
    This itself shouldn't really take any inputs (as in not have buttons and such)
    """
    def __init__(self, grid_width: int, grid_height: int):
        self.tick_counter = 0
        self.running = True

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.grid = self._create_empty_grid()

        self.food_sources = []
        self.food_items = []
        self._spawn_initial_food_sources()

        self.data_lock = threading.Lock()

        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.start()

    def _create_empty_grid(self):
        """Create a simple 2D grid initialized to 0."""
        return [
            [0 for _ in range(self.grid_width)] for _ in range(self.grid_height)
        ]

    def _spawn_initial_food_sources(self):
        mid_x = self.grid_width // 2 + 1
        mid_y = self.grid_height // 2 + 1

        spawn_locations = [
            (mid_x, mid_y),
            (mid_x - 2, mid_y - 2),
            (mid_x + 2, mid_y + 2),
            (mid_x - 2, mid_y + 2),
            (mid_x + 2, mid_y - 2)
        ]

        for x, y in spawn_locations:
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                grass_patch = SimpleGrassPatch(
                    position=(x, y),
                    area_id=1  # Default Area ID
                )
                self.food_sources.append(grass_patch)

    def _simulation_loop(self):
        while self.running:
            with self.data_lock:
                self.tick_counter += 1

                new_food_items = []
                for source in self.food_sources:
                    dropped_food = source.update()
                    if dropped_food:
                        new_food_items.append(dropped_food)

                self.food_items.extend(new_food_items)

                food_to_keep = []
                for food in self.food_items:
                    if not food.update():
                        food_to_keep.append(food)
                self.food_items = food_to_keep

            time.sleep(0.01)

    def set_grid_cell(self, x: int, y: int, value: int):
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            self.grid[y][x] = value

    def render(self, window: pygame.window, panel_x: int, panel_y: int, cell_size: int):
        """
        Function called every app tick to render.
        This is where the actual simulation should be displayed.
        """
        with self.data_lock:
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    cell_rect = pygame.Rect(
                        panel_x + x * cell_size,
                        panel_y + y * cell_size,
                        cell_size,
                        cell_size
                    )

                    if (x + y) % 2 == 0:
                        cell_color = (50, 50, 50)
                    else:
                        cell_color = (40, 40, 40)

                    pygame.draw.rect(window, cell_color, cell_rect)
                    pygame.draw.rect(window, (70, 70, 70), cell_rect, 1)

            for source in self.food_sources:
                source.render(window, cell_size)
            for food in self.food_items:
                food.render(window, cell_size)

            font = pygame.font.Font(None, 32)
            tick_text = font.render(f"Ticks: {self.tick_counter}", True, (255, 255, 255))
            food_count_text = font.render(
                f"Food items: {len(self.food_items)}", True, (255, 255, 255)
            )

            window.blit(tick_text, (panel_x + 10, panel_y + 10))
            window.blit(food_count_text, (panel_x + 10, panel_y + 90))

    def shutdown(self):
        self.running = False
        if self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1.0)
