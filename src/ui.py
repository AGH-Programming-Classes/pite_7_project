import pygame
import pygame_gui
from environment import Environment

# TODO spawn agent at mouse
# TODO spawn food source at mouse 
# TODO set map tile at mouse
# TODO reset simulation button
# TODO pause simulation button
# TODO log space

class UI:
    def __init__(self, manager: pygame_gui.UIManager, x: int, y: int, width: int, height: int):
        self.manager = manager

        margin = 10
        btn_height = 40
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(x, y, width, height),
            manager=self.manager,
            margins={
                'top': margin,
                'right': margin,
                'bottom': margin,
                'left': margin
            }
        )

        self.sim_ctrl_container = pygame_gui.core.UIContainer(
            relative_rect=pygame.Rect(0, -btn_height, self.panel.get_abs_rect().width - 2 * margin, btn_height),
            manager=manager,
            container=self.panel,
            anchors={
                'bottom': 'bottom'
            }
        )
       
        self.reset_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, 0, (self.sim_ctrl_container.get_abs_rect().width - 2 * margin) / 3, btn_height),
            text='Reset',
            manager=self.manager,
            container=self.sim_ctrl_container
        )

        self.pause_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(margin, 0, (self.sim_ctrl_container.get_abs_rect().width - 2 * margin) / 3, btn_height),
            text='Pause',
            manager=self.manager,
            container=self.sim_ctrl_container,
            anchors={
                'left': 'left',
                'left_target': self.reset_btn
            }
        )

        self.resume_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(margin, 0, (self.sim_ctrl_container.get_abs_rect().width - 2 * margin) / 3, btn_height),
            text='Resume',
            manager=self.manager,
            container=self.sim_ctrl_container,
            anchors={
                'left': 'left',
                'left_target': self.pause_btn
            }
        )
        
    def process_events(self, event: pygame.Event, env: Environment):
       pass 