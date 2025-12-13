"""Environment module containing the main simulation state."""
import threading
import time

import pygame
from food import FoodSource, SimpleGrassPatch, Food

GRID_WIDTH = 20
GRID_HEIGHT = 15
CELL_SIZE = 30 # Size of one grid cell in pixels

class Environment:
    """
    This is a de-facto container for global application state and
    has a "public" function called by the application game loop: render

    This should also expose all things that the user could do (like a button hit)
    This itself shouldn't really take any inputs (as in not have buttons and such)
    """
    def __init__(self):
        self.tick_counter = 0
        self.user_counter = 0
        self.running = True

        self.grid_size = (GRID_WIDTH, GRID_HEIGHT)
        self.cell_size = CELL_SIZE

        self.food_sources = [] 
        self.food_items = []   

        self._spawn_initial_food_sources()

        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.start()

    def _spawn_initial_food_sources(self):
        """Places initial food sources (e.g., grass patches) in the environment."""
        spawn_locations = [(7, 7), (10, 2), (15, 10), (5, 12)] 
        
        for x, y in spawn_locations:
            grass_patch = SimpleGrassPatch(
                (x, y), 
                area_id=1, # Default Area ID
                cell_size=self.cell_size
            )
            self.food_sources.append(grass_patch)

    def _simulation_loop(self):
        """
        This is where the actual simulation logic should be implemented.
        """
        while self.running:
            self.tick_counter += 1
    
            new_food_items = []
            for source in self.food_sources:
                dropped_food = source.update() 
                if dropped_food:
                    new_food_items.append(dropped_food)
            
            self.food_items.extend(new_food_items)
            
            # 2. Update Food Items (Age/Expiration)
            food_to_keep = []
            for food in self.food_items:
                if not food.update(): 
                    food_to_keep.append(food)
            self.food_items = food_to_keep

            time.sleep(0.01)

    # Section for user input
    # This is where all user input should be handled.
    # (like clicking a button, changing a slider value, etc.)

    def click_inc_button(self):
        """Handle increment button click."""
        self.user_counter += 1

    def render(self, window, panel_rect):
        """Function called every app tick to render.

        This is where the actual simulation should be displayed.
        """
        sim_width = self.grid_size[0] * self.cell_size
        sim_height = self.grid_size[1] * self.cell_size
        sim_rect = pygame.Rect(panel_rect.x, panel_rect.y, sim_width, sim_height)
        
        # Draw the simulation grid background (dark grey/black)
        pygame.draw.rect(window, (60, 60, 60), sim_rect)

        # Render Food Sources and Items (must be done before rendering the info panel)
        for source in self.food_sources:
            source.render(window, self.cell_size)
            
        for food in self.food_items:
            food.render(window, self.cell_size)
         
        #pygame.draw.rect(window, (60, 60, 60), panel_rect)
        font = pygame.font.Font(None, 32)

        tick_text = font.render(f"Ticks: {self.tick_counter}", True, (255, 255, 255))
        user_text = font.render(f"User counter: {self.user_counter}", True, (255, 255, 255))
        food_count_text = font.render(f"Food items: {len(self.food_items)}", True, (255, 255, 255))

        window.blit(tick_text, (panel_rect.x + 10, panel_rect.y + 10))
        window.blit(user_text, (panel_rect.x + 10, panel_rect.y + 50))
        window.blit(food_count_text, (panel_rect.x + 10, panel_rect.y + 90))
        
    def shutdown(self):
        """Tear down logic called before application exit."""
        self.running = False
