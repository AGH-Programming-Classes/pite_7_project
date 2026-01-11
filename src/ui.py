import pygame
import pygame_gui
from environment import Environment
from area import Area

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

        # spawn ui section
        self.spawn_ctrl_container = pygame_gui.elements.UIAutoResizingContainer(
            relative_rect=pygame.Rect(0, 0, self.panel.get_abs_rect().width - 2 * margin, 0),
            manager=self.manager,
            container=self.panel,
            resize_top=False,
            resize_right=False,
            resize_bottom=True,
            resize_left=False
        )

        self.spawn_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(0, 0, -1, -1),
            text='Spawn',
            manager=self.manager,
            container=self.spawn_ctrl_container,
            anchors={
                'centerx': 'centerx'
            }
        )

        self.spawn_agent_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, margin, (self.spawn_ctrl_container.get_abs_rect().width - margin) / 2, btn_height),
            text='Agent',
            manager=self.manager,
            container=self.spawn_ctrl_container,
            anchors={
                'top_target': self.spawn_label
            }
        )
        
        self.spawn_food_source_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(margin, margin, (self.spawn_ctrl_container.get_abs_rect().width - margin) / 2, btn_height),
            text='Food source',
            manager=self.manager,
            container=self.spawn_ctrl_container,
            anchors={
                'top_target': self.spawn_label,
                'left_target': self.spawn_agent_btn
            }
        )

        # set area ui section
        self.area_ctrl_container = pygame_gui.elements.UIAutoResizingContainer(
            relative_rect=pygame.Rect(0, margin, self.panel.get_abs_rect().width - 2 * margin, 200),
            manager=self.manager,
            container=self.panel,
            anchors={
                'top_target': self.spawn_ctrl_container
            }
        )

        self.area_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(0, 0, -1, -1),
            text='Area',
            manager=self.manager,
            container=self.area_ctrl_container,
            anchors={
                'centerx': 'centerx'
            }
        )

        self.area_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, margin, (self.spawn_ctrl_container.get_abs_rect().width - margin) / 3, btn_height),
            text='Set Area',
            manager=self.manager,
            container=self.area_ctrl_container,
            anchors={
                'top_target': self.area_label
            }
        )
        
        self.area_list = pygame_gui.elements.UIDropDownMenu(
            relative_rect=pygame.Rect(margin, margin, (self.spawn_ctrl_container.get_abs_rect().width - margin) / 3 * 2, btn_height),
            options_list=[area.display_name for area in list(Area)],
            starting_option=list(Area)[0].display_name,
            manager=self.manager,
            container=self.area_ctrl_container,
            anchors={
                'top_target': self.area_label,
                'left_target': self.area_btn
            }
        )

        # sim control ui section
        self.sim_ctrl_container = pygame_gui.core.UIContainer(
            relative_rect=pygame.Rect(0, -btn_height, self.panel.get_abs_rect().width - 2 * margin, btn_height),
            manager=manager,
            container=self.panel,
            anchors={
                'bottom': 'bottom'
            }
        )
       
        self.sim_reset_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, 0, (self.sim_ctrl_container.get_abs_rect().width - 2 * margin) / 3, btn_height),
            text='Reset',
            manager=self.manager,
            container=self.sim_ctrl_container
        )

        self.sim_pause_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(margin, 0, (self.sim_ctrl_container.get_abs_rect().width - 2 * margin) / 3, btn_height),
            text='Pause',
            manager=self.manager,
            container=self.sim_ctrl_container,
            anchors={
                'left_target': self.sim_reset_btn
            }
        )

        self.sim_resume_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(margin, 0, (self.sim_ctrl_container.get_abs_rect().width - 2 * margin) / 3, btn_height),
            text='Resume',
            manager=self.manager,
            container=self.sim_ctrl_container,
            anchors={
                'left_target': self.sim_pause_btn
            }
        )
        
        # current action label
        self.action_container = pygame_gui.elements.UIAutoResizingContainer(
            relative_rect=pygame.Rect(0, -btn_height, self.panel.get_abs_rect().width - 2 * margin, 0),
            manager=self.manager,
            container=self.panel,
            anchors={
                'bottom': 'bottom',
                'bottom_target': self.sim_ctrl_container
            }
        )

        self.action_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(0, 0, -1, -1),
            text='Current action:',
            manager=self.manager,
            container=self.action_container,
        )
        
        self.action_value = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(margin, 0, -1, -1),
            text='some action',
            manager=self.manager,
            container=self.action_container,
            anchors={
                'left_target': self.action_label
            }
        )
        
    def process_events(self, event: pygame.Event, env: Environment):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            match event.ui_element:
                case self.sim_resume_btn:
                    env.resume()
                case self.sim_pause_btn:
                    env.pause()
                case self.sim_reset_btn:
                    # TODO reset simulation
                    pass
