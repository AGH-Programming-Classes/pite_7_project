"""Environment module containing the main simulation state."""
import threading
import time

import pygame


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
        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.start()

    def _simulation_loop(self):
        """
        This is where the actual simulation logic should be implemented.
        """
        while self.running:
            self.tick_counter += 1
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
        pygame.draw.rect(window, (60, 60, 60), panel_rect)
        font = pygame.font.Font(None, 32)
        tick_text = font.render(f"Ticks: {self.tick_counter}", True, (255, 255, 255))
        user_text = font.render(f"User counter: {self.user_counter}", True, (255, 255, 255))
        window.blit(tick_text, (panel_rect.x + 10, panel_rect.y + 10))
        window.blit(user_text, (panel_rect.x + 10, panel_rect.y + 50))

    def shutdown(self):
        """Tear down logic called before application exit."""
        self.running = False
