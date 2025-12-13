"""Configuration module for the simulation."""

import yaml
from typing import Any

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