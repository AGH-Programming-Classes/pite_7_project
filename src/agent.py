"""Agent module containing the Agent class and related utilities for simulation."""
from __future__ import annotations
import math
import random
import pygame
import typing
import logging
if typing.TYPE_CHECKING:
    from environment import Environment
import uuid
from area import Area


def _clamp(x: float, lo: float, hi: float) -> float:
    """Clamps value x between lo and hi."""
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def _tanh(x: float) -> float:
    """Hyperbolic tangent activation function."""
    return math.tanh(x)


def _sqrt_scale(points: float, k: float) -> float:
    """Scales points using square root with coefficient k."""
    return k * math.sqrt(max(0.0, points))

def _sign(x: float):
    """Returns sign of value x."""
    return 1.0 if x >= 0 else -1.0

def dist2(ax: float, ay: float, bx: float, by: float) -> float:
    """Returns squared distance between (ax, ay) and (bx, by) in torus space."""
    dx, dy = torus_diff(ax, ay, bx, by)
    return dx * dx + dy * dy

def torus_diff(ax: float, ay: float, bx: float, by: float) -> typing.Tuple[float, float]:
    """Returns dirrection (dx, dy) from (ax, ay) to (bx, by) in torus space."""
    max_x = float(Agent.bound_x)
    max_y = float(Agent.bound_y)
    tx = float(bx - ax)
    ty = float(by - ay)
    dx = tx if abs(tx) < max_x / 2 else tx - _sign(tx) * max_x 
    dy = ty if abs(ty) < max_y / 2 else ty - _sign(ty) * max_y
    return (dx, dy)
     

class Agent:
    """Represents an agent in the simulation with neural network-based decision making."""

    # Sense vector (normalized inputs for neural network):
    # 0  hp_n            -> current HP / max HP (0..1)
    # 1  en_n            -> current energy / max energy (0..1)
    # 2  age_n           -> current age / max age (0..1)
    # 3  x_n             -> x position normalized to world width (0..1)
    # 4  y_n             -> y position normalized to world height (0..1)
    # 5  head_x          -> facing direction x (cos(angle))
    # 6  head_y          -> facing direction y (-sin(angle))
    # 7  food_d_n        -> dist2ance to nearest food normalized by sight (0..1)
    # 8  food_dx_n       -> x direction to nearest food (normalized)
    # 9  food_dy_n       -> y direction to nearest food (normalized)
    # 10 food_in_sight   -> whether food is within sight range (0 or 1)
    # 11 friend_count_n  -> nearby friends count (normalized)
    # 11 enemy_count_n   -> nearby enemies count (normalized)
    # 12 enemy_d_n       -> dist2ance to nearest enemy normalized by sight (0..1)
    # 13 enemy_dx_n      -> x direction to nearest enemy (normalized)
    # 14 enemy_dy_n      -> y direction to nearest enemy (normalized)
    # 15 ground          -> type of ground where agent actually is
    # 16 bias            -> constant bias input (always 1.0)
    bound_x = 0
    bound_y = 0
    cell_size = 1


    actions = {"ACTION_MOVE" : 0,
    "ACTION_MATE" : 1,
    "ACTION_ATTACK" : 2}

    body_points_total = 100

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    def __init__(self, position: tuple, environment : Environment,/, decision_matrix : typing.List[typing.List[int]] = None, genome = None, species = None ):
        from mating import Mating
        from sense import Sense

        self.environment = environment
        self.mate_module :Mating = Mating(self)
        self.sense_module : Sense = Sense(self)
        self.x = float(position[0])
        self.y = float(position[1])

        self.uuid = uuid.uuid4()

        self.group_id = species if species else random.randint(0,1)  # team/species id (same -> friend, different -> enemy)

        if genome:
            self.body_points = genome
        else:
            self.body_points = self._random_body_points(self.body_points_total)

        self.max_hp = 10.0 + _sqrt_scale(self.body_points["hp"], 2.0)
        self.max_energy = (10.0 + _sqrt_scale(self.body_points["energy"], 2.0)) * 2
        self.base_speed = 0.70+ _sqrt_scale(self.body_points["speed"], 0.28)
        self.attack_power = 0.5 + _sqrt_scale(self.body_points["attack"], 0.06)
        self.max_age = int((300 + _sqrt_scale(self.body_points["lifespan"], 18.0)) * 2.5)
        self.sight = 70.0 + _sqrt_scale(self.body_points["sight"], 6.0)
        self.agility = 30.0 + _sqrt_scale(self.body_points["agility"], 2.0)

        self.hp = self.max_hp
        self.energy = self.max_energy
        self.age = 0

        self.last_action = self.actions["ACTION_MOVE"]

        self.signal_active = False
        self.signal_timer = 0
        self.signal_duration = 20
        self.signal_range = 50.0

        self.suggested_action = None
        self.suggested_action_timer = 0
        self.suggested_action_duration = 50

        self.input_size = len(self.sense())
        self.action_count = len(self.actions)
        self.output_size = self.action_count + 2
        self.angle = random.random() * 360

        if decision_matrix:
            self.weights = decision_matrix
        else:
            self.weights = self._random_matrix(self.input_size, self.output_size, scale=0.6)



        self._inputs_override = None
        self._last_enemy = None
        self._last_food = None

    def _random_body_points(self, total: int):
        """Randomly dist2ribute total points across body stat keys."""
        keys = ["hp", "energy", "speed", "attack", "lifespan", "sight", "agility"]
        pts = {k: 0 for k in keys}
        for _ in range(total):
            pts[random.choice(keys)] += 1
        return pts

    def _random_matrix(self, n_in: int, n_out: int, scale: float):
        """Generate random neural network weight matrix."""
        return [[(random.random() * 2.0 - 1.0) * scale for _ in range(n_out)] for _ in range(n_in)]

    def set_inputs(self, inputs):
        """Override sensory inputs with manual vector for testing."""
        if inputs is None:
            self._inputs_override = None
            return
        if len(inputs) != self.input_size:
            raise ValueError(f"expected input vector length {self.input_size}, got {len(inputs)}")
        self._inputs_override = [float(v) for v in inputs]

    def sense(self, foods=None, agents=None):
        return self.sense_module.sense(foods, agents)

    def think(self, inputs):
        """Forward pass through neural network."""



        out = [0.0 for _ in range(self.output_size)]
        for i in range(self.input_size):
            xi = inputs[i]
            wi = self.weights[i]
            for j in range(self.output_size):
                out[j] += xi * wi[j]
        for j in range(self.output_size):
            out[j] = _tanh(out[j])
        return out

    def decide(self, outputs):
        logits = outputs[: self.action_count]
        best_i = 0
        best_v = logits[0]
        for i in range(1, self.action_count):
            if logits[i] > best_v:
                best_v = logits[i]
                best_i = i
        turn = outputs[self.action_count]
        intensity = outputs[self.action_count + 1]
        return best_i, turn, intensity


    def _move(self, turn: float, intensity: float, speed_modifier: float = 1.0):

        turn = (turn + 1) * math.pi

        inten = _clamp(0.5 + 0.5 * intensity, 0.0, 1.0)
        sp = self.base_speed * (0.20 + 1.30 * inten) * speed_modifier

        self.x = (self.x + math.cos(turn) * sp) % (self.environment.grid_width * self.environment.cell_size)
        self.y = (self.y - math.sin(turn) * sp) % (self.environment.grid_height * self.environment.cell_size)

        cost = 0.0075 + 0.035 * inten
        self.energy = max(0.0, self.energy - cost)

        self.angle = math.degrees(turn)



    def _attack(self):
        self.energy = max(0.0, self.energy - 0.16)
        agents = self.environment.agents
        if agents:
            r2 = self.sight * self.sight
            best_enemy_d2 = 1e18
            best_enemy = None

            for a in agents:
                if a is self:
                    continue
                ax = float(getattr(a, "x", 0.0))
                ay = float(getattr(a, "y", 0.0))
                d2 = dist2(self.x, self.y, ax, ay)
                if d2 > r2:
                    continue
                same_group = getattr(a, "group_id", None) == self.group_id
                if same_group:
                    continue
                else:
                    if d2 < best_enemy_d2:
                        best_enemy_d2 = d2
                        best_enemy : Agent = a
            if best_enemy:
                best_enemy.hp -= self.attack_power
                best_enemy.signal()
            

    def _mate(self):
        self.mate_module.mate()

    def signal(self):
        """Send signal to call nearby teammates for help."""
        self.signal_active = True
        self.signal_timer = self.signal_duration
        
        nearby_agents = self.environment.get_nearby_agents(self, self.signal_range)
        same_species = [agent for agent in nearby_agents 
                       if agent is not self and agent.group_id == self.group_id]
        
        affected_agents = random.sample(same_species, min(3, len(same_species)))
        
        for agent in affected_agents:
            agent.signal_active = True
            agent.signal_timer = self.signal_duration
            agent.suggested_action = self.actions["ACTION_MOVE"]
            agent.suggested_action_timer = agent.suggested_action_duration


    def _tick_body(self):
        self.age += 1
        self.energy = max(0.0, self.energy - 0.01)
        if self.energy <= 0.01:
            self.hp = max(0.0, self.hp - 0.03)
        if self.age >= self.max_age:
            self.hp = 0.0
        
        if self.signal_active and self.signal_timer > 0:
            self.signal_timer -= 1
        if self.signal_timer <= 0:
            self.signal_active = False
        
        if self.suggested_action_timer > 0:
            self.suggested_action_timer -= 1
        if self.suggested_action_timer <= 0:
            self.suggested_action = None

    def is_alive(self) -> bool:
        return self.hp > 0.0 and self.energy > 0

    def update(self, speed_modifier):
        if not self.is_alive():
            return

        if self._inputs_override is None:
            nearby_agents = self.environment.get_nearby_agents(self, self.sight * 2)
            inputs = self.sense(self.environment.food_sources, nearby_agents)
        else:
            inputs = self._inputs_override

        outputs = self.think(inputs)
        action, turn, intensity = self.decide(outputs)

        if action == self.actions["ACTION_MOVE"]:
            self.logger.debug(f"Agent - {self.uuid}; action - move")
            self._move(turn, intensity, speed_modifier)
        elif action == self.actions["ACTION_MATE"]:
            self.logger.debug(f"Agent - {self.uuid}; action - mate")
            self._mate()
        else:
            self.logger.debug(f"Agent - {self.uuid}; action - attack")
            self._attack()

        self.last_action = action / 3


        self._tick_body()

    def render(self, window: pygame.window, cell_size: int, offset: tuple):
        offset_x, offset_y = offset

        env_x = offset_x + self.x
        env_y = offset_y + self.y
        r = max(2.0, cell_size * 0.25)

        points = []
        rad = math.radians(self.angle)
        points.append((env_x + math.cos(rad) * r, env_y - math.sin(rad) * r))

        rad = math.radians(self.angle + 135.0)
        points.append((env_x + math.cos(rad) * r, env_y - math.sin(rad) * r))

        rad = math.radians(self.angle + 180.0)
        points.append((env_x + math.cos(rad) * r * 0.5, env_y - math.sin(rad) * r * 0.5))

        rad = math.radians(self.angle - 135.0)
        points.append((env_x + math.cos(rad) * r, env_y - math.sin(rad) * r))

        color = (100, 200, 255) if self.group_id == 0 else (255, 255, 255)  
        pygame.draw.polygon(window, color, points)

        bar_w = int(cell_size * 0.8)
        bar_h = max(2, int(cell_size * 0.12))
        px = int(env_x - bar_w * 0.5)
        py = int(env_y - r - bar_h - 2)

        hp_n = _clamp(self.hp / max(1e-9, self.max_hp), 0.0, 1.0)
        en_n = _clamp(self.energy / max(1e-9, self.max_energy), 0.0, 1.0)

        pygame.draw.rect(window, (40, 40, 40), pygame.Rect(px, py, bar_w, bar_h))
        pygame.draw.rect(window, (0, 200, 0), pygame.Rect(px, py, int(bar_w * hp_n), bar_h))

        py2 = py + bar_h + 2
        pygame.draw.rect(window, (40, 40, 40), pygame.Rect(px, py2, bar_w, bar_h))
        pygame.draw.rect(window, (70, 160, 240), pygame.Rect(px, py2, int(bar_w * en_n), bar_h))
