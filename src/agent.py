"""Agent module containing the Agent class and related utilities for simulation."""

import math
import random
import pygame
import typing
import logging
if typing.TYPE_CHECKING:
    from environment import Environment
import uuid

def _clamp(x: float, lo: float, hi: float) -> float:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def _tanh(x: float) -> float:
    return math.tanh(x)


def _sqrt_scale(points: float, k: float) -> float:
    return k * math.sqrt(max(0.0, points))


def _dist2(ax: float, ay: float, bx: float, by: float) -> float:
    dx = ax - bx
    dy = ay - by
    return dx * dx + dy * dy



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


def _dist2(ax: float, ay: float, bx: float, by: float) -> float:
    """Returns squared Euclidean distance between (ax, ay) and (bx, by)."""
    dx = ax - bx
    dy = ay - by
    return dx * dx + dy * dy


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
    # 7  food_d_n        -> distance to nearest food normalized by sight (0..1)
    # 8  food_dx_n       -> x direction to nearest food (normalized)
    # 9  food_dy_n       -> y direction to nearest food (normalized)
    # 10 friend_count_n  -> nearby friends count (normalized)
    # 11 enemy_count_n   -> nearby enemies count (normalized)
    # 12 enemy_d_n       -> distance to nearest enemy normalized by sight (0..1)
    # 13 enemy_dx_n      -> x direction to nearest enemy (normalized)
    # 14 enemy_dy_n      -> y direction to nearest enemy (normalized)
    # 15 bias            -> constant bias input (always 1.0)
    bound_x = 0
    bound_y = 0
    cell_size = 1


    actions = {"ACTION_MOVE" : 0,
    "ACTION_IDLE" : 1,
    "ACTION_FLEE" : 2,
    "ACTION_MATE" : 3,
    "ACTION_ATTACK" : 4}

    body_points_total = 100

    distance_to_partner_to_mate = 0.05
    #parameters to reproduction
    chance_for_mutation = 0.05
    mutation_multiply_border = 0.2 # random.uniform(1-var,1+var)
    mutation_addding_border = 0.05

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    def __init__(self, position: tuple, environment : Environment,/, decision_matrix : typing.List[typing.List[int]] = None, genome = None ):
        self.environment = environment
        self.x = float(position[0])
        self.y = float(position[1])

        self.uuid = uuid.uuid4()

        self.group_id = random.randint(0, 1)  # team/species id (same -> friend, different -> enemy)

        if genome:
            self.body_points = genome
        else:
            self.body_points = self._random_body_points(self.body_points_total)

        self.max_hp = 10.0 + _sqrt_scale(self.body_points["hp"], 2.0)
        self.max_energy = (10.0 + _sqrt_scale(self.body_points["energy"], 2.0)) * 5
        self.base_speed = 0.5 + _sqrt_scale(self.body_points["speed"], 0.2)
        self.attack_power = 0.5 + _sqrt_scale(self.body_points["attack"], 0.06)
        self.max_age = int(200 + _sqrt_scale(self.body_points["lifespan"], 14.0)) * 5
        self.sight = 70.0 + _sqrt_scale(self.body_points["sight"], 6.0)
        self.agility = 30.0 + _sqrt_scale(self.body_points["agility"], 2.0)

        self.hp = self.max_hp
        self.energy = self.max_energy
        self.age = 0

        self.angle = random.random() * 360.0
        self.last_action = self.actions["ACTION_MOVE"]

        self.input_size = len(self.sense())
        self.action_count = len(self.actions)
        self.output_size = self.action_count + 2

        if decision_matrix:
            self.weights = decision_matrix
        else:
            self.weights = self._random_matrix(self.input_size, self.output_size, scale=0.6)


        self._inputs_override = None
        self._last_enemy = None
        self._last_food = None

    def _random_body_points(self, total: int):
        """Randomly distribute total points across body stat keys."""
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
        """Generate normalized sensory input vector."""
        bx = float(self.bound_x) if self.bound_x > 0 else 1.0
        by = float(self.bound_y) if self.bound_y > 0 else 1.0

        hp_n = _clamp(self.hp / max(1e-9, self.max_hp), 0.0, 1.0)
        en_n = _clamp(self.energy / max(1e-9, self.max_energy), 0.0, 1.0)
        age_n = _clamp(self.age / max(1, self.max_age), 0.0, 1.0)

        x_n = _clamp(self.x / max(1e-9, bx), 0.0, 1.0)  # normalized position
        y_n = _clamp(self.y / max(1e-9, by), 0.0, 1.0)

        ang = math.radians(self.angle)
        head_x = math.cos(ang)  # facing direction (unit vector)
        head_y = -math.sin(ang)

        food_d_n, food_dx_n, food_dy_n, food_in_sigth = 1.0, 0.0, 0.0, 0
        if foods:
            best_d2 = 1e18
            best = None
            for f in foods:
                fx = float(getattr(f, "x", 0.0))
                fy = float(getattr(f, "y", 0.0))
                d2 = _dist2(self.x, self.y, fx, fy)
                if d2 < best_d2:
                    best_d2 = d2
                    best = (fx, fy)
            if best is not None:
                dx = best[0] - self.x
                dy = best[1] - self.y
                d = math.sqrt(best_d2)
                food_d_n = _clamp(d / max(1e-9, self.sight), 0.0, 1.0)
                food_dx_n = _clamp(dx / max(1e-9, self.sight), -1.0, 1.0)
                food_dy_n = _clamp(dy / max(1e-9, self.sight), -1.0, 1.0)
                self._last_food = best
                if d <= self.sight: # Adding boolean to deal with semantic discontinuity ( 1 could mean food is far away and 0,95 mean is really close)
                    food_in_sigth = 1

        friend_count_n = 0.0
        friend_d_n, friend_dx_n, friend_dy_n = 1.0, 0.0, 0.0
        enemy_count_n = 0.0
        enemy_d_n, enemy_dx_n, enemy_dy_n = 1.0, 0.0, 0.0

        if agents:
            r2 = self.sight * self.sight
            friends = 0
            enemies = 0
            best_friend_d2 = 1e18
            best_friend = None 
            best_enemy_d2 = 1e18
            best_enemy = None

            for a in agents:
                if a is self:
                    continue
                ax = float(getattr(a, "x", 0.0))
                ay = float(getattr(a, "y", 0.0))
                d2 = _dist2(self.x, self.y, ax, ay)
                if d2 > r2:
                    continue

                same_group = getattr(a, "group_id", None) == self.group_id
                if same_group:
                    friends += 1
                    if d2 < best_friend_d2:
                        best_friend_d2 = d2
                        best_friend = (ax, ay)
                else:
                    enemies += 1
                    if d2 < best_enemy_d2:
                        best_enemy_d2 = d2
                        best_enemy = (ax, ay)

            friend_count_n = _clamp(friends / 10.0, 0.0, 1.0)
            enemy_count_n = _clamp(enemies / 10.0, 0.0, 1.0)

            if best_enemy is not None:
                dx = best_enemy[0] - self.x
                dy = best_enemy[1] - self.y
                d = math.sqrt(best_enemy_d2)
                enemy_d_n = _clamp(d / max(1e-9, self.sight), 0.0, 1.0)
                enemy_dx_n = _clamp(dx / max(1e-9, self.sight), -1.0, 1.0)
                enemy_dy_n = _clamp(dy / max(1e-9, self.sight), -1.0, 1.0)
                self._last_enemy = best_enemy
            else:
                self._last_enemy = None

            
            if best_friend is not None: # Adding this part to enable to agent getting information where are friends
                dx = best_friend[0] - self.x
                dy = best_friend[1] - self.y
                d = math.sqrt(best_friend_d2)
                friend_d_n = _clamp(d / max(1e-9, self.sight), 0.0, 1.0)
                friend_dx_n = _clamp(dx / max(1e-9, self.sight), -1.0, 1.0)
                friend_dy_n = _clamp(dy / max(1e-9, self.sight), -1.0, 1.0)
                self._last_friend = best_friend
            else:
                self._last_friend = None

            


        return [
            hp_n,
            en_n,
            age_n,
            x_n,
            y_n,
            head_x,
            head_y,
            food_d_n,
            food_dx_n,
            food_dy_n,
            food_in_sigth,
            friend_count_n,
            friend_d_n,
            friend_dx_n,
            friend_dy_n,
            enemy_count_n,
            enemy_d_n,
            enemy_dx_n,
            enemy_dy_n,
            1.0,
        ]

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

    def _apply_bounds(self, new_x: float, new_y: float, new_angle: float):
        """Apply world boundary conditions with reflection."""
        bx = float(self.bound_x)
        by = float(self.bound_y)
        if bx <= 0 or by <= 0:
            self.x, self.y, self.angle = new_x, new_y, new_angle % 360.0
            return

        max_x = max(0.0, bx - 1e-6)
        max_y = max(0.0, by - 1e-6)

        if new_x < 0.0 or new_x >= bx:
            new_x = -new_x if new_x < 0.0 else (2.0 * max_x - new_x)
            new_angle = 180.0 - new_angle

        if new_y < 0.0 or new_y >= by:
            new_y = -new_y if new_y < 0.0 else (2.0 * max_y - new_y)
            new_angle = 360.0 - new_angle

        self.x = max(0.0, min(new_x, max_x))
        self.y = max(0.0, min(new_y, max_y))
        self.angle = new_angle % 360.0

    def _move(self, turn: float, intensity: float, speed_modifier: float = 1.0):
        turn_delta = turn * (self.agility * 0.5)
        new_angle = self.angle + turn_delta

        inten = _clamp(0.5 + 0.5 * intensity, 0.0, 1.0)
        sp = self.base_speed * (0.20 + 1.30 * inten) * speed_modifier

        rad = math.radians(new_angle)
        new_x = self.x + math.cos(rad) * sp
        new_y = self.y - math.sin(rad) * sp
        self._apply_bounds(new_x, new_y, new_angle)

        cost = 0.02 + 0.06 * inten
        self.energy = max(0.0, self.energy - cost)

    def _idle(self):
        self.energy = min(self.max_energy, self.energy - 0.01)

    def _flee(self, turn: float, intensity: float):
        if self._last_enemy is None:
            self._move(turn, intensity)
            return
        ex, ey = self._last_enemy
        dx = self.x - float(ex)
        dy = self.y - float(ey)
        ang = math.degrees(math.atan2(-dy, dx))
        self.angle = ang % 360.0
        self._move(0.0, max(0.2, intensity))

    def _attack(self):
        self.energy = max(0.0, self.energy - 0.08)

    def _mate(self):
        from environment import Environment
        self.energy = max(0.0, self.energy - 0.3)
        agents : typing.List[Agent] = self.environment.get_agents()
        close_agents : typing.List[Agent] = []
        for ag in agents:
            if _dist2(ag.x, ag.y, self.x, self.y) < self.distance_to_partner_to_mate:
                close_agents.append(ag)
        if len(close_agents) > 0:
            matrix, vector = self.create_new_genes( random.choice(close_agents))
            self.environment.create_agent(Agent((self.x, self.y), self.environment, decision_matrix = matrix, genome = vector))


    def _tick_body(self):
        self.age += 1
        self.energy = max(0.0, self.energy - 0.01)
        if self.energy <= 0.01:
            self.hp = max(0.0, self.hp - 0.03)
        if self.age >= self.max_age:
            self.hp = 0.0

    def is_alive(self) -> bool:
        return self.hp > 0.0

    def update(self):
        if not self.is_alive():
            return

        if self._inputs_override is None:
            inputs = self.sense()
        else:
            inputs = self._inputs_override

        outputs = self.think(inputs)
        action, turn, intensity = self.decide(outputs)
        self.last_action = action

        if action == self.actions["ACTION_MOVE"]:
            self.logger.debug(f"Agent - {self.uuid}; action - move")
            self._move(turn, intensity)
        elif action == self.actions["ACTION_IDLE"]:
            self.logger.debug(f"Agent - {self.uuid}; action - idle")
            self._idle()
        elif action == self.actions["ACTION_FLEE"]:
            self.logger.debug(f"Agent - {self.uuid}; action - free")
            self._flee(turn, intensity)
        elif action == self.actions["ACTION_MATE"]:
            self.logger.debug(f"Agent - {self.uuid}; action - mate")
            self._mate()
        else:
            self.logger.debug(f"Agent - {self.uuid}; action - attack")
            self._attack()

        self._tick_body()

    def create_new_genes(self, second : Agent):
        matrix =  self.create_new_decision_matrix(second)
        vector = self.create_new_genome_vector(second)

        numbers_to_change_in_matrix = int(len(matrix) * len(matrix[0]) / (1 / self.chance_for_mutation))

        #Applying mutation - there could be multiply of value or adding

        for _ in range(numbers_to_change_in_matrix):
            row = random.choice(matrix)
            i = random.randint(0, len(row)-1)
            if random.random() < 0.2:
                row[i] *= random.uniform(1 - self.mutation_multiply_border, 1 + self.mutation_multiply_border)
            else:
                row[i] += random.uniform(-self.mutation_addding_border, self.mutation_addding_border)

        for _ in range(int(len(vector) / (1 / self.chance_for_mutation))):
            item = random.choice(vector.keys())
            if random.random() < 0.2:
                vector[item] *= random.uniform(1 - self.mutation_multiply_border, 1 + self.mutation_multiply_border)
            else:
                vector[item] += random.uniform(-self.mutation_addding_border, self.mutation_addding_border)

        #Normalisation of vector

        normalisation = 100 / sum(vector.values())
        for key,value in vector.items():
            vector[key] = value * normalisation


        return matrix, vector
        
    def create_new_decision_matrix(self, second : Agent):
        output = []
        for i in range(len(self.weights)):
            number = random.randint(0, len(self.weights[0]))
            output.append(self.weights[i][:number] + self.weights[i][number:])
        return output

    def create_new_genome_vector(self, second : Agent):
        genome = self.body_points.copy()
        for item in genome.keys():
            genome[item] = self.body_points[item] if random.randint(0,1) == 1 else second.body_points[item]
        return genome

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

        pygame.draw.polygon(window, (255, 255, 255), points)

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
