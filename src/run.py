"""Main application entry point for the simulation."""
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIPanel
import config
from environment import Environment
from area import Area


pygame.init()
pygame.display.set_caption("Simulation")
screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

clock = pygame.time.Clock()
manager = pygame_gui.UIManager((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))

FOOD_COLORS = {
    "Grass": (100, 200, 100),
    "Berry": (150, 70, 160),
    "Fruit": (125, 200, 50),
    "Cactus": (190, 165, 50)
}
HERBIVORE_DOT = (0, 200, 0)

sidebar_width = config.PANEL_X
ui_panel = UIPanel(relative_rect=pygame.Rect(0, 0, sidebar_width, config.WINDOW_HEIGHT),
                    manager=manager, starting_height=1)

button_pairs = [
    ("Grass", Area.PLAINS),
    ("Berry", Area.BERRY_CORNER),
    ("Fruit", Area.FERTILE_VALLEY),
    ("Cactus", Area.DESERT)
]

ui_elements = []
y_offset = 10
btn_w = (sidebar_width - 30) // 2
btn_h = (sidebar_width - 30) // 2

for food_str, area_obj in button_pairs:
    pair_color = area_obj.color

    btn_food = UIButton(relative_rect=pygame.Rect(10, y_offset, btn_w, btn_h),
                        text="", manager=manager, container=ui_panel)
    btn_food.colours['normal_bg'] = pygame.Color(pair_color)
    btn_food.rebuild()
    ui_elements.append({"btn": btn_food, "value": food_str})

    btn_area = UIButton(relative_rect=pygame.Rect(10 + btn_w + 10, y_offset, btn_w, btn_h),
                        text="", manager=manager, container=ui_panel)
    btn_area.colours['normal_bg'] = pygame.Color(pair_color)
    btn_area.rebuild()
    ui_elements.append({"btn": btn_area, "value": area_obj})

    y_offset += btn_h + 10

current_brush = None

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

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for item in ui_elements:
                if event.ui_element == item["btn"]:
                    current_brush = item["value"]

        if event.type == pygame.MOUSEBUTTONDOWN:
            sim_rect = pygame.Rect(config.PANEL_X,
                                    config.PANEL_Y,
                                    config.PANEL_WIDTH,
                                    config.PANEL_HEIGHT)
            if sim_rect.collidepoint(mouse_pos):
                grid_x = (mouse_pos[0] - config.PANEL_X) // config.CELL_SIZE
                grid_y = (mouse_pos[1] - config.PANEL_Y) // config.CELL_SIZE
                if current_brush:
                    if isinstance(current_brush, Area):
                        env.change_area_at(grid_x, grid_y, current_brush)
                    else:
                        env.add_manual_food_source(grid_x, grid_y, current_brush)
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

    for item in ui_elements:
        btn_rect = item["btn"].get_abs_rect()

        if isinstance(item["value"], str):
            dot_pos = btn_rect.center
            pygame.draw.circle(screen, HERBIVORE_DOT, dot_pos, 7)
            pygame.draw.circle(screen, (0, 0, 0), dot_pos, 7, 1)

        if item["value"] == current_brush:
            pygame.draw.rect(screen, (255, 255, 255), btn_rect, 3)

    pygame.display.flip()

pygame.quit()
