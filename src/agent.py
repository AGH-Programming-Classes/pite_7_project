"""Agent module containing the Agent class and related utilities for simulation."""
from __future__ import annotations

import logging
import math
import random
import typing
import uuid
from collections import deque

import pygame

from area import Area
from food import FoodSource

if typing.TYPE_CHECKING:
    from environment import Environment


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


def _sign(x: float) -> float:
    """Returns sign of value x."""
    return 1.0 if x >= 0 else -1.0


def dist2(ax: float, ay: float, bx: float, by: float) -> float:
    """Returns squared distance between (ax, ay) and (bx, by) in torus space."""
    dx, dy = torus_diff(ax, ay, bx, by)
    return dx * dx + dy * dy


def torus_diff(ax: float, ay: float, bx: float, by: float) -> typing.Tuple[float, float]:
    """Returns direction (dx, dy) from (ax, ay) to (bx, by) in torus space."""
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
    # 0  hp_n
    # 1  en_n
    # 2  age_n
    # 3  x_n
    # 4  y_n
    # 5  head_x
    # 6  head_y
    # 7  food_d_n
    # 8  food_dx_n
    # 9  food_dy_n
    # 10 food_in_sight (0/1)  <-- kluczowa flaga od kolegi
    # 11 friend_count_n
    # 12 friend_d_n
    # 13 friend_dx_n
    # 14 friend_dy_n
    # 15 friend_in_sight (0/1)  <-- dodane analogicznie
    # 16 enemy_count_n
    # 17 enemy_d_n
    # 18 enemy_dx_n
    # 19 enemy_dy_n
    # 20 enemy_in_sight (0/1)   <-- dodane analogicznie
    # 21 ground
    # 22 loop_n (0..1)          <-- detekcja kręcenia kółek (pomocniczy sygnał)
    # 23 bias (1.0)

    bound_x = 0
    bound_y = 0
    cell_size = 1

    actions = {
        "ACTION_MOVE": 0,
        "ACTION_IDLE": 1,
        "ACTION_FLEE": 2,
        "ACTION_MATE": 3,
        "ACTION_ATTACK": 4,
    }

    body_points_total = 100

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    # --- anti-loop / drift tuning ---
    _HISTORY_LEN = 40               # ile ostatnich pozycji trzymamy
    _MIN_PROGRESS_PX = 12.0         # poniżej tej "drogi netto" uznajemy, że jest pętla/stagnacja
    _LOOP_CONFIRM_STEPS = 25        # ile klatek musi to trwać, żeby uznać pętlę
    _DRIFT_MAX_DEG = 20.0           # maksymalny dryf w stopniach (nie robi chaosu)
    _DRIFT_STEP_DEG = 2.0           # jak szybko dryf się zmienia
    _DRIFT_DECAY = 0.85             # jak szybko dryf zanika, gdy nie ma problemu

    def __init__(
        self,
        position: tuple,
        environment: "Environment",
        /,
        decision_matrix: typing.List[typing.List[float]] | None = None,
        genome=None,
        species=None,
    ):
        from mating import Mating

        self.environment = environment
        self.mate_module: Mating = Mating(self)
        self.x = float(position[0])
        self.y = float(position[1])

        self.uuid = uuid.uuid4()
        self.group_id = species if species is not None else random.randint(0, 1)

        if genome:
            self.body_points = genome
        else:
            self.body_points = self._random_body_points(self.body_points_total)

        self.max_hp = 10.0 + _sqrt_scale(self.body_points["hp"], 2.0)
        self.max_energy = (10.0 + _sqrt_scale(self.body_points["energy"], 2.0)) * 2
        self.base_speed = 0.5 + _sqrt_scale(self.body_points["speed"], 0.2)
        self.attack_power = 0.5 + _sqrt_scale(self.body_points["attack"], 0.06)
        self.max_age = int(200 + _sqrt_scale(self.body_points["lifespan"], 14.0)) * 2
        self.sight = 70.0 + _sqrt_scale(self.body_points["sight"], 6.0)
        self.agility = 30.0 + _sqrt_scale(self.body_points["agility"], 2.0)

        self.hp = self.max_hp
        self.energy = self.max_energy
        self.age = 0

        self.angle = random.random() * 360.0
        self.last_action = self.actions["ACTION_MOVE"]

        # --- memory for anti-loop ---
        self._pos_history: deque[tuple[float, float]] = deque(maxlen=self._HISTORY_LEN)
        self._loop_counter = 0
        self._drift_deg = 0.0

        self._inputs_override = None
        self._last_enemy = None
        self._last_food = None
        self._last_friend = None

        # infer input size from sense vector
        self.input_size = len(self.sense())
        self.action_count = len(self.actions)
        self.output_size = self.action_count + 2

        if decision_matrix:
            self.weights = self._normalize_or_rebuild_weights(decision_matrix)
        else:
            self.weights = self._random_matrix(self.input_size, self.output_size, scale=0.6)

    def _normalize_or_rebuild_weights(self, decision_matrix: typing.List[typing.List[float]]):
        """
        Backward compatibility: if someone passes a matrix with wrong shape,
        we rebuild it to the correct input_size/output_size.
        """
        try:
            rows = len(decision_matrix)
            cols = len(decision_matrix[0]) if rows else 0
        except Exception:
            rows, cols = 0, 0

        if rows == self.input_size and cols == self.output_size:
            return decision_matrix

        # Rebuild to avoid runtime IndexError in think()
        rebuilt = self._random_matrix(self.input_size, self.output_size, scale=0.6)
        min_r = min(rows, self.input_size)
        min_c = min(cols, self.output_size)
        for i in range(min_r):
            for j in range(min_c):
                rebuilt[i][j] = float(decision_matrix[i][j])
        return rebuilt

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

    def _net_progress(self) -> float:
        """Net displacement over history window."""
        if len(self._pos_history) < 2:
            return 1e9
        x0, y0 = self._pos_history[0]
        x1, y1 = self._pos_history[-1]
        dx, dy = torus_diff(x0, y0, x1, y1)
        return math.sqrt(dx * dx + dy * dy)

    def _update_loop_state(self, has_target_in_sight: bool) -> float:
        """
        Returns loop_n in [0..1]. Increases when agent doesn't make progress and has no target.
        """
        self._pos_history.append((self.x, self.y))

        if has_target_in_sight:
            self._loop_counter = max(0, self._loop_counter - 2)
            return _clamp(self._loop_counter / float(self._LOOP_CONFIRM_STEPS), 0.0, 1.0)

        progress = self._net_progress()
        if progress < self._MIN_PROGRESS_PX and len(self._pos_history) >= self._LOOP_CONFIRM_STEPS:
            self._loop_counter = min(self._LOOP_CONFIRM_STEPS, self._loop_counter + 1)
        else:
            self._loop_counter = max(0, self._loop_counter - 1)

        return _clamp(self._loop_counter / float(self._LOOP_CONFIRM_STEPS), 0.0, 1.0)

    def sense(self, foods=None, agents=None):
        """Generate normalized sensory input vector."""
        bx = float(self.bound_x) if self.bound_x > 0 else 1.0
        by = float(self.bound_y) if self.bound_y > 0 else 1.0

        hp_n = _clamp(self.hp / max(1e-9, self.max_hp), 0.0, 1.0)
        en_n = _clamp(self.energy / max(1e-9, self.max_energy), 0.0, 1.0)
        age_n = _clamp(self.age / max(1, self.max_age), 0.0, 1.0)

        x_n = _clamp(self.x / max(1e-9, bx), 0.0, 1.0)
        y_n = _clamp(self.y / max(1e-9, by), 0.0, 1.0)

        ang = math.radians(self.angle)
        head_x = math.cos(ang)
        head_y = -math.sin(ang)

        # --- food ---
        food_d_n, food_dx_n, food_dy_n, food_in_sight = 1.0, 0.0, 0.0, 0
        if foods:
            best_d2 = 1e18
            best = None
            for f in foods:
                fx = float(getattr(f, "x", 0.0))
                fy = float(getattr(f, "y", 0.0))
                d2 = dist2(self.x, self.y, fx, fy)
                if d2 < best_d2:
                    best_d2 = d2
                    best = (fx, fy)
            if best is not None:
                dx, dy = torus_diff(self.x, self.y, best[0], best[1])
                d = math.sqrt(best_d2)

                # Normalizacja dystansu: nadal clamp 0..1, ale boolean mówi "czy w zasięgu"
                food_d_n = _clamp(d / max(1e-9, self.sight), 0.0, 1.0)
                food_dx_n = _clamp(dx / max(1e-9, self.sight), -1.0, 1.0)
                food_dy_n = _clamp(dy / max(1e-9, self.sight), -1.0, 1.0)
                self._last_food = best
                if d <= self.sight:
                    food_in_sight = 1

        # --- friends / enemies ---
        friend_count_n = 0.0
        friend_d_n, friend_dx_n, friend_dy_n, friend_in_sight = 1.0, 0.0, 0.0, 0
        enemy_count_n = 0.0
        enemy_d_n, enemy_dx_n, enemy_dy_n, enemy_in_sight = 1.0, 0.0, 0.0, 0

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
                d2 = dist2(self.x, self.y, ax, ay)
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
                dx, dy = torus_diff(self.x, self.y, best_enemy[0], best_enemy[1])
                d = math.sqrt(best_enemy_d2)
                enemy_d_n = _clamp(d / max(1e-9, self.sight), 0.0, 1.0)
                enemy_dx_n = _clamp(dx / max(1e-9, self.sight), -1.0, 1.0)
                enemy_dy_n = _clamp(dy / max(1e-9, self.sight), -1.0, 1.0)
                self._last_enemy = best_enemy
                if d <= self.sight:
                    enemy_in_sight = 1
            else:
                self._last_enemy = None

            if best_friend is not None:
                dx, dy = torus_diff(self.x, self.y, best_friend[0], best_friend[1])
                d = math.sqrt(best_friend_d2)
                friend_d_n = _clamp(d / max(1e-9, self.sight), 0.0, 1.0)
                friend_dx_n = _clamp(dx / max(1e-9, self.sight), -1.0, 1.0)
                friend_dy_n = _clamp(dy / max(1e-9, self.sight), -1.0, 1.0)
                self._last_friend = best_friend
                if d <= self.sight:
                    friend_in_sight = 1
            else:
                self._last_friend = None

        cell = self.environment._get_agent_area(self)
        if cell == Area.PLAINS:
            ground = 0.0
        elif cell == Area.FERTILE_VALLEY:
            ground = 0.9
        elif cell == Area.DESERT:
            ground = 0.1
        elif cell == Area.BERRY_CORNER:
            ground = 1.0
        else:
            raise ValueError(f"Wrong place! {cell}, {type(cell)}")

        # loop detector: tylko jeśli nie ma celu w zasięgu
        has_target_in_sight = bool(food_in_sight or enemy_in_sight or friend_in_sight)
        loop_n = self._update_loop_state(has_target_in_sight=has_target_in_sight)

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
            float(food_in_sight),
            friend_count_n,
            friend_d_n,
            friend_dx_n,
            friend_dy_n,
            float(friend_in_sight),
            enemy_count_n,
            enemy_d_n,
            enemy_dx_n,
            enemy_dy_n,
            float(enemy_in_sight),
            ground,
            loop_n,
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
        """Apply torus effect (link right to left and top to bottom)."""
        bx = float(self.bound_x)
        by = float(self.bound_y)
        if bx <= 0 or by <= 0:
            self.x, self.y, self.angle = new_x, new_y, new_angle % 360.0
            return

        max_x = max(0.0, bx - 1e-6)
        max_y = max(0.0, by - 1e-6)

        self.x = (new_x + bx) % max_x
        self.y = (new_y + by) % max_y
        self.angle = new_angle % 360.0

    def _update_drift(self, loop_n: float):
        """
        Lekki dryf: gdy loop_n rośnie, dryf rośnie (mała losowa korekta kierunku),
        gdy loop_n maleje, dryf zanika.
        """
        if loop_n > 0.5:
            # random-walk drift
            step = random.uniform(-self._DRIFT_STEP_DEG, self._DRIFT_STEP_DEG)
            self._drift_deg = _clamp(self._drift_deg + step, -self._DRIFT_MAX_DEG, self._DRIFT_MAX_DEG)
        else:
            # decay to 0
            self._drift_deg *= self._DRIFT_DECAY
            if abs(self._drift_deg) < 0.05:
                self._drift_deg = 0.0

    def _move(self, turn: float, intensity: float, speed_modifier: float = 1.0, loop_n: float = 0.0):
        # turn from network + drift if looping
        self._update_drift(loop_n)

        turn_delta = turn * (self.agility * 0.5)
        new_angle = self.angle + turn_delta + self._drift_deg * loop_n

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
        dx, dy = torus_diff(ex, ey, self.x, self.y)
        ang = math.degrees(math.atan2(-dy, dx))
        self.angle = ang % 360.0
        self._move(0.0, max(0.2, intensity))

    def _attack(self):
        self.energy = max(0.0, self.energy - 0.08)

    def _mate(self):
        self.mate_module.mate()

    def _tick_body(self):
        self.age += 1
        self.energy = max(0.0, self.energy - 0.01)
        if self.energy <= 0.01:
            self.hp = max(0.0, self.hp - 0.03)
        if self.age >= self.max_age:
            self.hp = 0.0

    def is_alive(self) -> bool:
        return self.hp > 0.0 and self.energy > 0

    def update(self, speed_modifier):
        if not self.is_alive():
            return

        if self._inputs_override is None:
            inputs = self.sense(self.environment.food_sources, self.environment.get_agents())
        else:
            inputs = self._inputs_override

        outputs = self.think(inputs)
        action, turn, intensity = self.decide(outputs)
        self.last_action = action

        # loop_n jest na przedostatniej pozycji (przed bias)
        loop_n = float(inputs[-2])

        if action == self.actions["ACTION_MOVE"]:
            self.logger.debug(f"Agent - {self.uuid}; action - move")
            self._move(turn, intensity, speed_modifier=speed_modifier, loop_n=loop_n)
        elif action == self.actions["ACTION_IDLE"]:
            self.logger.debug(f"Agent - {self.uuid}; action - idle")
            self._idle()
        elif action == self.actions["ACTION_FLEE"]:
            self.logger.debug(f"Agent - {self.uuid}; action - flee")
            self._flee(turn, intensity)
        elif action == self.actions["ACTION_MATE"]:
            self.logger.debug(f"Agent - {self.uuid}; action - mate")
            self._mate()
        else:
            self.logger.debug(f"Agent - {self.uuid}; action - attack")
            self._attack()

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
