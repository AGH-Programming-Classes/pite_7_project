"""Main application entry point for the simulation."""
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIPanel
import config
from environment import Environment
from area import Area
from food import FoodSource
from ui import UI

pygame.init()
pygame.display.set_caption("Simulation")
screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

clock = pygame.time.Clock()
manager = pygame_gui.UIManager((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
env_ui = UI(
    manager=manager,
    x=config.PANEL_WIDTH + 2*config.PANEL_X,
    y=0,
    width=config.WINDOW_WIDTH - (config.PANEL_WIDTH + 2*config.PANEL_X),
    height=config.WINDOW_HEIGHT
)

env = Environment(
    grid_width=config.GRID_WIDTH,
    grid_height=config.GRID_HEIGHT,
    pixel_width=config.PANEL_WIDTH,
    pixel_height=config.PANEL_HEIGHT
)

running = True
while running:
    dt = clock.tick(60) / 1000.0
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            env.shutdown()
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            sim_rect = pygame.Rect(config.PANEL_X,
                                    config.PANEL_Y,
                                    config.PANEL_WIDTH,
                                    config.PANEL_HEIGHT)
            if sim_rect.collidepoint(mouse_pos):
                grid_x = (mouse_pos[0] - config.PANEL_X) // config.CELL_SIZE
                grid_y = (mouse_pos[1] - config.PANEL_Y) // config.CELL_SIZE
                if env_ui.current_brush:
                    if isinstance(env_ui.current_brush, Area):
                        env.change_area_at(grid_x, grid_y, env_ui.current_brush)
                    elif isinstance(env_ui.current_brush, type(FoodSource)):
                        env.add_manual_food_source(grid_x, grid_y, env_ui.current_brush)
        manager.process_events(event)
        env_ui.process_events(event, env)

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
