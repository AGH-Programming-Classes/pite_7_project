"""Agent module"""

import random
import math
import pygame

class Agent:
    """Represents agent that can interact with environment"""
    bound_x = 0 # environment size
    bound_y = 0

    def __init__(self, position: tuple):
        self.x, self.y = position
        self.angle = 0 # agent 'head' direction in degrees, between 0-359, 0 points right
        self.speed = 10 # how fast agent moves
        self.agility = 20 # max change of agent direction

    def _random_walk(self):
        """Calculates new position in random direction"""
        new_angle = self.angle + self.agility * (random.random() - 0.5)
        rad = math.radians(new_angle)
        new_x = self.x + math.cos(rad) * self.speed
        new_y = self.y - math.sin(rad) * self.speed

        self._check_bounds((new_x, new_y), new_angle)

    def _check_bounds(self, new_position: tuple, new_angle: int):
        """Keeps agent within bounds"""
        new_x, new_y = new_position
        if new_x > self.bound_x or new_x < 0:
            new_x = (2 * self.bound_x - new_x) % self.bound_x
            new_angle = 180 - new_angle

        if new_y > self.bound_y or new_y < 0:
            new_y = (2 * self.bound_y - new_y) % self.bound_y
            new_angle = 360 - new_angle

        self.x, self.y = new_x, new_y
        self.angle = new_angle % 360

    def update(self):
        """Updates agent position"""
        self._random_walk()

    def render(self, window: pygame.window, cell_size: int, offset: tuple):
        """Renders agent on screen"""
        offset_x, offset_y = offset
        env_x = self.x + offset_x
        env_y = self.y + offset_y
        r = cell_size / 4

        points = []
        rad = math.radians(self.angle)
        head_x = env_x + math.cos(rad) * r
        head_y = env_y - math.sin(rad) * r
        points.append((head_x, head_y))
        rad = math.radians(self.angle + 135)
        left_tail_x = env_x + math.cos(rad) * r
        left_tail_y = env_y - math.sin(rad) * r
        points.append((left_tail_x, left_tail_y))
        rad = math.radians(self.angle + 180)
        center_x = env_x + math.cos(rad) * r / 2
        center_y = env_y - math.sin(rad) * r / 2
        points.append((center_x, center_y))
        rad = math.radians(self.angle - 135)
        right_tail_x = env_x + math.cos(rad) * r
        right_tail_y = env_y - math.sin(rad) * r
        points.append((right_tail_x, right_tail_y))

        pygame.draw.polygon(window, (255, 255, 255), points)
