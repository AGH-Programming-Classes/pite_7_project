from enum import Enum

class Area(Enum):
    PLAINS = {"id": 1,
            "display_name": "Plains", 
            "agent_speed_modifier": 1.0,
            "food_regen_modifier": 1.2, 
            "expansion_chance": 0.003, 
            "color": (60, 120, 60), 
            "max_food_sources": 5}
    FERTILE_VALLEY = {"id": 2,
                    "display_name": "Fertile Valley", 
                    "agent_speed_modifier": 0.9,
                    "food_regen_modifier": 1.5, 
                    "expansion_chance": 0.001, 
                    "color": (80, 160, 80), 
                    "max_food_sources": 5}
    DESERT = {"id": 3,
              "display_name": 
              "Desert", 
              "agent_speed_modifier": 1.2,
              "food_regen_modifier": 0.5, 
              "expansion_chance": 0.0005, 
              "color": (200, 180, 50), 
              "max_food_sources": 5}
    BERRY_CORNER = {"id": 4,
                    "display_name": "Berry Corner", 
                    "agent_speed_modifier": 1.0,
                    "food_regen_modifier": 1.2, 
                    "expansion_chance": 0.007, 
                    "color": (180, 100, 255), 
                    "max_food_sources": 5}

    def __init__(self, config):
        self.id = config["id"]
        self.display_name = config["display_name"]
        self.agent_speed_modifier = config["agent_speed_modifier"]
        self.food_regen_modifier = config["food_regen_modifier"]
        self.expansion_chance = config["expansion_chance"]
        self.color = config["color"]
        self.max_food_sources = config["max_food_sources"]
