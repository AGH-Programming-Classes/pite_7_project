"""Environment module containing the main simulation state."""

import threading
import time
import random
from typing import List, Tuple
import pygame
from food import SimpleGrassPatch, Food, BerryBush, FertileFruitTree, CactusPads
from agent import Agent
from area import Area
from terrain import generate_terrain

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
        self.pause_sim = False

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.grid = self._create_empty_grid()

        self.pixel_width = pixel_width
        self.pixel_height = pixel_height
        self.cell_size = max(1, self.pixel_width // self.grid_width)

        self.terrain = generate_terrain(
            width=self.grid_width,
            height=self.grid_height,
        )

        self.food_sources = []
        self.food_items = []

        self.area_food_sources = {
            area: 0 for area in Area
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

    def _cleanup_at(self, x: int, y: int):
        """Deletes food source and all food it has generated at location (x, y)."""
        with self.data_lock:
            for fs in self.food_sources:
                if fs.x == x and fs.y == y:
                    fs.destroy()

            self.food_sources = [fs for fs in self.food_sources if not fs.is_destroyed]

            self.food_items = [f for f in self.food_items if not (f.x == x and f.y == y)]

    def add_manual_food_source(self, grid_x: int, grid_y: int, source_type: str):
        mapping = {
            "Grass": (SimpleGrassPatch, Area.PLAINS),
            "Berry": (BerryBush, Area.BERRY_CORNER),
            "Fruit": (FertileFruitTree, Area.FERTILE_VALLEY),
            "Cactus": (CactusPads, Area.DESERT)
        }

        if source_type not in mapping:
            return
        cls, target_area = mapping[source_type]

        self._cleanup_at(grid_x, grid_y)

        with self.data_lock:
            if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
                self.terrain[grid_y][grid_x] = target_area
                new_source = cls(position=(grid_x, grid_y),
                                 area=target_area,
                                 env_area_counters=self.area_food_sources)
                self.food_sources.append(new_source)
                self.area_food_sources[target_area] += 1

    def change_area_at(self, grid_x: int, grid_y: int, new_area: Area):
        self._cleanup_at(grid_x, grid_y)

        with self.data_lock:
            if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
                self.terrain[grid_y][grid_x] = new_area
    def is_food_source_at(self, x: int, y: int) -> bool:
        """Returns if food_source at location"""
        return any(fs.x == x and fs.y == y and not fs.is_destroyed for fs in self.food_sources)

    def count_food_sources_in_area(self, area: Area) -> int:
        """Returns how many food sources in area"""
        return sum(1 for fs in self.food_sources if fs.area == area)

    def get_area_at(self, x: int, y: int) -> Area:
        """Returns area at location"""
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            return self.terrain[y][x]
        return Area.PLAINS

    def _cells_for_area(self, area: Area) -> List[Tuple[int, int]]:
        """Returns list of (x, y) coordinates that belong to the given area."""
        return [
            (x, y)
            for y in range(self.grid_height)
            for x in range(self.grid_width)
            if self.terrain[y][x] == area
        ]


    def _spawn_initial_food_sources(self):
        spawn_plan = {
            Area.PLAINS: (SimpleGrassPatch, 4),
            Area.FERTILE_VALLEY: (FertileFruitTree, 3),
            Area.DESERT: (CactusPads, 3),
            Area.BERRY_CORNER: (BerryBush, 3),
        }

        for area, (cls, desired_count) in spawn_plan.items():
            available_cells = self._cells_for_area(area)
            if not available_cells:
                continue

            random.shuffle(available_cells)
            allowed = min(
                desired_count,
                len(available_cells),
                area.max_food_sources - self.area_food_sources[area]
            )
            for x, y in available_cells[:allowed]:
                if self.is_food_source_at(x, y):
                    continue
                self.food_sources.append(
                    cls(
                        position=(x, y),
                        area=area,
                        env_area_counters=self.area_food_sources
                    )
                )
                self.area_food_sources[area] += 1



    def _spawn_initial_agents(self):
        Agent.bound_x = self.pixel_width
        Agent.bound_y = self.pixel_height
        Agent.cell_size = self.cell_size

        for _ in range(50):
            pos_x = random.randint(0, Agent.bound_x)
            pos_y = random.randint(0, Agent.bound_y)
            agent = Agent((pos_x, pos_y), self)
            self.agents.append(agent)

    def _simulation_loop(self):
        while self.running:
            time.sleep(0.01)

            if self.pause_sim:
                continue
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
                            and self.area_food_sources[source.area] < source.area.max_food_sources
                        ):
                            cls = type(source)
                            new_source = cls(position=(new_x, new_y),
                                            area=source.area,
                                            env_area_counters=self.area_food_sources)
                            self.food_sources.append(new_source)
                            self.area_food_sources[source.area] += 1

                self.food_sources = [fs for fs in self.food_sources if not fs.is_destroyed]
                self.food_items.extend(new_food_items)

                food_to_keep = []
                for food in self.food_items:
                    if not food.update():
                        food_to_keep.append(food)
                self.food_items = food_to_keep

                for agent in self.agents:
                    area = self._get_agent_area(agent)
                    speed_modifier = getattr(area, "agent_speed_modifier", 1.0)
                    agent.update(speed_modifier)
                    self._feed_agent(agent)


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

    def pause(self):
        self.pause_sim = True

    def resume(self):
        self.pause_sim = False

    def get_agents(self):
        return self.agents

    #This function should deal with creating new agents
    def create_agent(self, agent : Agent):
        pass
        # self.agents.append(agent)
    def _get_agent_area(self, agent: Agent) -> Area:
        """Maps agent pixel position to the underlying terrain cell."""
        grid_x = min(self.grid_width - 1, max(0, int(agent.x // self.cell_size)))
        grid_y = min(self.grid_height - 1, max(0, int(agent.y // self.cell_size)))
        return self.get_area_at(grid_x, grid_y)

    def _get_agent_grid_pos(self, agent: Agent) -> tuple[int, int]:
        """Maps agent pixel position to integer grid coordinates."""
        grid_x = min(self.grid_width - 1, max(0, int(agent.x // self.cell_size)))
        grid_y = min(self.grid_height - 1, max(0, int(agent.y // self.cell_size)))
        return grid_x, grid_y

    def _feed_agent(self, agent: Agent) -> None:
        """If agent stands on food, consume one item and restore energy."""
        grid_x, grid_y = self._get_agent_grid_pos(agent)
        for i, food in enumerate(self.food_items):
            if food.x == grid_x and food.y == grid_y:
                agent.energy = min(agent.max_energy, agent.energy + food.value)
                agent.hp = min(agent.max_hp, agent.hp + 0.1 * food.value)
                del self.food_items[i]
                break
