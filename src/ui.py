import pygame
import pygame_gui
from environment import Environment
from area import Area, AREA_FOOD_SOURCE_MAPPING
from agent import Agent

class UI:
    def __init__(self, manager: pygame_gui.UIManager, x: int, y: int, width: int, height: int):
        self.current_brush = None
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
            container=self.panel
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
            relative_rect=pygame.Rect(0, margin, self.spawn_ctrl_container.get_abs_rect().width, btn_height),
            text='Agent',
            manager=self.manager,
            container=self.spawn_ctrl_container,
            anchors={
                'top_target': self.spawn_label
            }
        )

        self.spawn_food_source_container = pygame_gui.elements.UIAutoResizingContainer(
            relative_rect=pygame.Rect(0, 0, self.spawn_ctrl_container.get_abs_rect().width, 0),
            manager=self.manager,
            container=self.spawn_ctrl_container,
            anchors={
                'top_target': self.spawn_agent_btn
            }
        )

        self.spawn_food_source_btns = dict()
        y_offset = margin
        for area in list(Area):
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(0, y_offset, btn_height, btn_height),
                text='',
                manager=self.manager,
                container=self.spawn_food_source_container,

            )
            btn.colours['normal_bg'] = pygame.Color(area.color)
            btn.rebuild()
            label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(margin, y_offset, -1, btn_height),
                text=AREA_FOOD_SOURCE_MAPPING[area].__name__,
                manager=self.manager,
                container=self.spawn_food_source_container,
                anchors={
                    'left_target': btn
                }
            )
            self.spawn_food_source_btns[btn] = AREA_FOOD_SOURCE_MAPPING[area]
            y_offset += margin + btn_height
        
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

        self.set_area_btns_container = pygame_gui.elements.UIAutoResizingContainer(
            relative_rect=pygame.Rect(0, 0, self.area_ctrl_container.get_abs_rect().width, 0),
            manager=self.manager,
            container=self.area_ctrl_container,
            anchors={
                'top_target': self.area_label
            }
        )

        self.set_area_btns = dict()
        y_offset = margin
        for area in list(Area):
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(0, y_offset, btn_height, btn_height),
                text='',
                manager=self.manager,
                container=self.set_area_btns_container,

            )
            btn.colours['normal_bg'] = pygame.Color(area.color)
            btn.rebuild()
            label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(margin, y_offset, -1, btn_height),
                text=area.display_name,
                manager=self.manager,
                container=self.set_area_btns_container,
                anchors={
                    'left_target': btn
                }
            )
            self.set_area_btns[btn] = area
            y_offset += margin + btn_height
           

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
            text='Current brush:',
            manager=self.manager,
            container=self.action_container,
        )
        
        self.action_value = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(margin, 0, -1, -1),
            text='',
            manager=self.manager,
            container=self.action_container,
            anchors={
                'left_target': self.action_label
            }
        )

    def process_events(self, event: pygame.Event, env: Environment):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.sim_resume_btn:
                env.resume()
            elif event.ui_element == self.sim_pause_btn:
                env.pause()
            elif event.ui_element == self.sim_reset_btn:
                # TODO reset simulation
                pass
            elif event.ui_element == self.spawn_agent_btn:
                self.change_brush(Agent, 'Agent')
            elif event.ui_element in self.set_area_btns:
               area = self.set_area_btns[event.ui_element]
               self.change_brush(area, area.display_name)
            elif event.ui_element in self.spawn_food_source_btns:
                food_source = self.spawn_food_source_btns[event.ui_element]
                self.change_brush(food_source, food_source.__name__)

    def change_brush(self, new_brush, brush_name: str):
        self.current_brush = new_brush
        self.action_value.set_text(brush_name)

        
