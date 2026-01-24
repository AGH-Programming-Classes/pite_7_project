"""Configuration module for the simulation."""

import yaml

with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

WINDOW_WIDTH = cfg["window"]["width"]
WINDOW_HEIGHT = cfg["window"]["height"]

PANEL_X = cfg["panel"]["x"]
PANEL_Y = cfg["panel"]["y"]
PANEL_WIDTH = cfg["panel"]["width"]
PANEL_HEIGHT = cfg["panel"]["height"]

CELL_SIZE = cfg["grid"]["cell_size"]
GRID_WIDTH = PANEL_WIDTH // CELL_SIZE
GRID_HEIGHT = PANEL_HEIGHT // CELL_SIZE

CHART_AREA_HEIGHT = cfg["chart"]["height"]

MIN_AGE_PERCENT = cfg["mating"]["min_age_percent"]
MIN_ENERGY_LEVEL = cfg["mating"]["min_energy_level"]
MAX_RANGE = cfg["mating"]["max_range"]
MUTATION_CHANCE = cfg["mating"]["mutation_chance"]
MUTATION_MULTIPLY_BORDER = cfg["mating"]["mutation_multiply_border"] 
MUTATION_ADDING_BORDER = cfg["mating"]["mutation_addding_border"]

INITIAL_AGENT_COUNT = cfg["environment"]["initial_agent_count"]
INITIAL_FOOD_COUNT = cfg["environment"]["initial_food_count"]

DUMP = cfg["dump"]["dump"]
FILE_NAME = cfg["dump"]["file_name"]
MAX_TICK = cfg["dump"]["max_tick"]