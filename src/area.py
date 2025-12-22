class Area:
    def __init__(self, area_id, name, agent_speed_modifier, food_regen_modifier, expansion_chance, color, max_food_sources=5):
        self.id = area_id
        self.name = name
        self.agent_speed_modifier = agent_speed_modifier
        self.food_regen_modifier = food_regen_modifier
        self.expansion_chance = expansion_chance
        self.color = color
        self.max_food_sources = max_food_sources
        self.current_food_sources = 0 