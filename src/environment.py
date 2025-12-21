"""Environment module containing the main simulation state."""

import threading
import time
import random
import pygame
from food import SimpleGrassPatch,Food,BerryBush,FertileFruitTree,CactusPads
from agent import Agent
from area import Area

class Environment:
    """
    This is a de-facto container for global application state and
    has a "public" function called by the application game loop: render

    This should also expose all things that the user could do (like a button hit)
    This itself shouldn't really take any inputs (as in not have buttons and such)
    """
    def __init__(self, grid_width: int, grid_height: int, pixel_width: int, pixel_height: int):
        self.tick_counter = 0
        self.running = True

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.grid = self._create_empty_grid()

        self.pixel_width = pixel_width
        self.pixel_height = pixel_height

        self.food_sources = []
        self.food_items = []
        self.areas = {
            1: Area(1, "Plains",
                     agent_speed_modifier=1.0,
                       food_regen_modifier=1.2,
                         expansion_chance=0.003,
                           color=(60,120,60)),
            2: Area(2,
                     "Fertile Valley",
                       agent_speed_modifier=0.9,
                         food_regen_modifier=1.5,
                           expansion_chance=0.001,
                             color=(80,160,80)),
            3: Area(3,
                     "Desert",
                       agent_speed_modifier=1.2,
                         food_regen_modifier=0.5,
                           expansion_chance=0.0005,
                             color=(200,180,50)),
            4: Area(4,
                     "Berry Corner",
                       agent_speed_modifier=1.0,
                         food_regen_modifier=1.2,
                           expansion_chance=0.007,
                             color=(180,100,255))
        }

        self._spawn_initial_food_sources()

        self.agents = []
        self._spawn_initial_agents()

        self.data_lock = threading.Lock()

        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.start()

    def _create_empty_grid(self):
        """Create a simple 2D grid initialized to 0."""
        return [
            [0 for _ in range(self.grid_width)] for _ in range(self.grid_height)
        ]

    def is_food_source_at(self, x: int, y: int) -> bool:
        """Returns if food_source at location"""
        return any(fs.x == x and fs.y == y and not fs.is_destroyed for fs in self.food_sources)

    def count_food_sources_in_area(self, area: Area) -> int:
        """Returns how many food sources in area"""
        return sum(1 for fs in self.food_sources if fs.area == area)

    def get_area_at(self, x, y) -> Area:
        """Returns area at location"""
        mid_x = self.grid_width // 2
        mid_y = self.grid_height // 2

        if x < mid_x and y < mid_y:
            return self.areas[1]  # top-left
        if x >= mid_x and y < mid_y:
            return self.areas[2]  # top-right
        if x < mid_x and y >= mid_y:
            return self.areas[3]  # bottom-left
        return self.areas[4]  # bottom-right


    def _spawn_initial_food_sources(self):
        mid_x = self.grid_width // 2
        mid_y = self.grid_height // 2

        corners = {
            1: (0, 0, mid_x - 1, mid_y - 1),
            2: (mid_x, 0, self.grid_width - 1, mid_y - 1),
            3: (0, mid_y, mid_x - 1, self.grid_height - 1),
            4: (mid_x, mid_y, self.grid_width - 1, self.grid_height - 1)
        }

        initial_sources = [
            (SimpleGrassPatch, 1, [(2, 2), (4, 4)]),
            (FertileFruitTree, 2, [(mid_x + 1, 1), (mid_x + 3, 3)]),
            (CactusPads, 3, [(2, mid_y + 1), (4, mid_y + 3)]),
            (BerryBush, 4, [(mid_x + 1, mid_y + 1), (mid_x + 3, mid_y + 3)])
        ]

        for cls, area_id, positions in initial_sources:
            area = self.areas[area_id]
            x_min, y_min, x_max, y_max = corners[area_id]

            existing_in_area = [fs for fs in self.food_sources if fs.area == area]
            if not existing_in_area:
                for x, y in positions:
                    if x_min <= x <= x_max and y_min <= y <= y_max:
                        if not self.is_food_source_at(x, y):
                            self.food_sources.append(cls(position=(x, y), area=area))



    def _spawn_initial_agents(self):
        Agent.bound_x = self.pixel_width
        Agent.bound_y = self.pixel_height

        for _ in range(5):
            pos_x = random.randint(0, Agent.bound_x)
            pos_y = random.randint(0, Agent.bound_y)
            agent = Agent((pos_x, pos_y))
            self.agents.append(agent)

    def _simulation_loop(self):
        while self.running:
            with self.data_lock:
                self.tick_counter += 1

                new_food_items = []
                for source in self.food_sources:
                    result = source.update()

                    if source.is_destroyed:
                        self.food_items = [f for f in self.food_items if
                        (f.x, f.y) != (source.x, source.y)]
                        continue

                    if isinstance(result, Food):
                        new_food_items.append(result)

                    if random.random() < getattr(source.area, 'expansion_chance', 0):
                        dx = random.randint(-3, 3)
                        dy = random.randint(-3, 3)
                        new_x = source.x + dx
                        new_y = source.y + dy

                        if (
                            0 <= new_x < self.grid_width
                            and 0 <= new_y < self.grid_height
                            and not self.is_food_source_at(new_x, new_y)
                            and self.get_area_at(new_x, new_y) == source.area
                            and source.area.current_food_sources < source.area.max_food_sources
                        ):
                            cls = type(source)
                            new_source = cls(position=(new_x, new_y), area=source.area)
                            self.food_sources.append(new_source)
                            source.area.current_food_sources += 1

                self.food_items.extend(new_food_items)

                food_to_keep = []
                for food in self.food_items:
                    if not food.update():
                        food_to_keep.append(food)
                self.food_items = food_to_keep

                for agent in self.agents:
                    agent.update()

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

                    area = self.get_area_at(x,y)
                    cell_color = area.color

                    pygame.draw.rect(window, cell_color, cell_rect)
                    pygame.draw.rect(window, (40, 40, 40), cell_rect, 1)

            for source in self.food_sources:
                source.render(window, cell_size, self.food_items, (panel_x, panel_y))
            for food in self.food_items:
                food.render(window, cell_size, panel_x, panel_y)

            for agent in self.agents:
                agent.render(window, cell_size, (panel_x, panel_y))

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
