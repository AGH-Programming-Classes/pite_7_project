"""Main application entry point for the simulation."""
import pygame
import pygame_gui
from pygame_gui.elements import UIButton
import yaml
from environment import Environment

with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

W = cfg["window"]["width"]
H = cfg["window"]["height"]

pygame.init()
pygame.display.set_caption("Simulation")
screen = pygame.display.set_mode((W, H))

clock = pygame.time.Clock()

manager = pygame_gui.UIManager((W, H))
env = Environment()
env_panel = pygame.Rect(cfg["panel"]["x"], cfg["panel"]["y"],
                        cfg["panel"]["width"], cfg["panel"]["height"])
btn_x = cfg["panel"]["x"] + cfg["panel"]["width"] + 20
btn_y = cfg["panel"]["y"]
inc_button = UIButton(
    relative_rect=pygame.Rect(btn_x, btn_y, 150, 50),
    text="Increment",
    manager=manager,
)

running = True
while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        # handle inputs
        if event.type == pygame.QUIT:
            env.shutdown()
            running = False
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == inc_button:
                env.click_inc_button()
        manager.process_events(event)

    manager.update(dt)
    env.render(screen, env_panel)
    manager.draw_ui(screen)
    pygame.display.flip()

pygame.quit()
