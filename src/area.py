from enum import Enum

class Area(Enum):
    PLAINS = (1, "Plains", 1.0, 1.2, 0.003, (60, 120, 60), 5)
    FERTILE_VALLEY = (2, "Fertile Valley", 0.9, 1.5, 0.001, (80, 160, 80), 5)
    DESERT = (3, "Desert", 1.2, 0.5, 0.0005, (200, 180, 50), 5)
    BERRY_CORNER = (4, "Berry Corner", 1.0, 1.2, 0.007, (180, 100, 255), 5)

    def __init__(self, area_id, display_name, agent_speed_modifier,
                  food_regen_modifier, expansion_chance, color, max_food_sources=5):
        self.id = area_id
        self.display_name = display_name
        self.agent_speed_modifier = agent_speed_modifier
        self.food_regen_modifier = food_regen_modifier
        self.expansion_chance = expansion_chance
        self.color = color
        self.max_food_sources = max_food_sources
