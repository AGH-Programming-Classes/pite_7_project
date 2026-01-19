"""Main application entry point for the simulation."""
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIPanel
import config
from environment import Environment
from area import Area
from food import FoodSource
from ui import UI
import charts
from agent import Agent

pygame.init()
pygame.display.set_caption("Simulation")
screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

clock = pygame.time.Clock()
manager = pygame_gui.UIManager((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
hint_font = pygame.font.Font(None, 22)


def _format_first_sample_age() -> str:
    age = charts.first_sample_age()
    if age <= 0:
        return ""
    if age < 60:
        return f"Oldest sample is {int(age)}s old"
    minutes = int(age // 60)
    seconds = int(age % 60)
    return f"Oldest sample is {minutes}m {seconds}s old"


def _chart_hint_text() -> str:
    base = "Scroll over the chart area to pan charts"
    age_text = _format_first_sample_age()
    return f"{base} — {age_text}" if age_text else base
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

chart_rect = pygame.Rect(
    config.PANEL_X,
    config.PANEL_Y + config.PANEL_HEIGHT + 20,
    config.PANEL_WIDTH,
    config.CHART_AREA_HEIGHT
)
chart_hint_pos = (chart_rect.x, chart_rect.bottom + 4)

charts.register_chart(
    name="Agents over time",
    value_name="Agents",
    callback=env.agent_count,
)
charts.register_chart(
    name="Average health",
    value_name="HP",
    callback=env.average_agent_health,
)
charts.register_chart(
    name="Average energy",
    value_name="Energy",
    callback=env.average_agent_energy,
)
charts.register_chart(
    name="Food sources with stock",
    value_name="Sources",
    callback=env.food_sources_with_stock,
)
charts.register_chart(
    name="Stored food across sources",
    value_name="Food",
    callback=env.total_food_stock,
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
                pixel_x = (mouse_pos[0] - config.PANEL_X)
                pixel_y = (mouse_pos[1] - config.PANEL_Y)
                grid_x = pixel_x // config.CELL_SIZE
                grid_y = pixel_y // config.CELL_SIZE
                if env_ui.current_brush:
                    if isinstance(env_ui.current_brush, Area):
                        env.change_area_at(grid_x, grid_y, env_ui.current_brush)
                    elif isinstance(env_ui.current_brush, type(FoodSource)):
                        env.add_manual_food_source(grid_x, grid_y, env_ui.current_brush)
                    elif isinstance(env_ui.current_brush, type(Agent)):
                        agent = Agent((pixel_x, pixel_y), env)
                        env.create_agent(agent)
        elif event.type == pygame.MOUSEWHEEL:
            if chart_rect.collidepoint(mouse_pos):
                charts.scroll(-event.y)
        manager.process_events(event)
        env_ui.process_events(event, env)

    manager.update(dt)
    charts.update(dt)

    screen.fill((20, 20, 20)) # Clear screen

    env.render(
        window=screen,
        panel_x=config.PANEL_X,
        panel_y=config.PANEL_Y,
        cell_size=config.CELL_SIZE
    )

    charts.render(screen, chart_rect)
    hint_surface = hint_font.render(_chart_hint_text(), True, (220, 220, 220))
    screen.blit(hint_surface, chart_hint_pos)

    manager.draw_ui(screen)

    pygame.display.flip()

pygame.quit()
