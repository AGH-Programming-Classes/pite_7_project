"""Main application entry point for the simulation."""
import pygame
import pygame_gui
import config
from environment import Environment


pygame.init()
pygame.display.set_caption("Simulation")
screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

clock = pygame.time.Clock()

manager = pygame_gui.UIManager((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

env = Environment(
    grid_width=config.GRID_WIDTH,
    grid_height=config.GRID_HEIGHT,
    pixel_width=config.PANEL_WIDTH,
    pixel_height=config.PANEL_HEIGHT
)

running = True
while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            env.shutdown()
            running = False

        manager.process_events(event)

    manager.update(dt)

    screen.fill((20, 20, 20)) # Clear screen

    env.render(
        window=screen,
        panel_x=config.PANEL_X,
        panel_y=config.PANEL_Y,
        cell_size=config.CELL_SIZE
    )

    manager.draw_ui(screen)
    pygame.display.flip()

pygame.quit()
