import math
import random
import pygame


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


class Agent:
    bound_x = 0
    bound_y = 0

    ACTION_MOVE = 0
    ACTION_IDLE = 1
    ACTION_FLEE = 2
    ACTION_MATE = 3
    ACTION_ATTACK = 4

    def __init__(self, position: tuple):
        self.x = float(position[0])
        self.y = float(position[1])

        self.angle = random.random() * 360.0
        self.last_action = self.ACTION_MOVE

        self.body_points_total = 100
        self.body_points = self._random_body_points(self.body_points_total)

        self.max_hp = 10.0 + _sqrt_scale(self.body_points["hp"], 2.0)
        self.max_energy = 10.0 + _sqrt_scale(self.body_points["energy"], 2.0)
        self.base_speed = 0.05 + _sqrt_scale(self.body_points["speed"], 0.02)
        self.attack_power = 0.5 + _sqrt_scale(self.body_points["attack"], 0.06)
        self.max_age = int(200 + _sqrt_scale(self.body_points["lifespan"], 14.0))
        self.sight = 2.0 + _sqrt_scale(self.body_points["sight"], 0.35)

        self.hp = self.max_hp
        self.energy = self.max_energy
        self.age = 0

        self.agility = 30.0 + _sqrt_scale(self.body_points["agility"], 2.0)

        self.input_size = 16
        self.action_count = 5
        self.output_size = self.action_count + 2

        self.W = self._random_matrix(self.input_size, self.output_size, scale=0.6)

        self._inputs_override = None
        self._last_target = None

    def _random_body_points(self, total: int):
        keys = ["hp", "energy", "speed", "attack", "lifespan", "sight", "agility"]
        pts = {k: 0 for k in keys}
        for _ in range(total):
            pts[random.choice(keys)] += 1
        return pts

    def _random_matrix(self, n_in: int, n_out: int, scale: float):
        return [[(random.random() * 2.0 - 1.0) * scale for _ in range(n_out)] for _ in range(n_in)]

    def set_inputs(self, inputs):
        if inputs is None:
            self._inputs_override = None
            return
        if len(inputs) != self.input_size:
            raise ValueError(f"expected input vector length {self.input_size}, got {len(inputs)}")
        self._inputs_override = [float(x) for x in inputs]

    def sense(self, foods=None, agents=None):
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

        food_d_n, food_dx_n, food_dy_n = 1.0, 0.0, 0.0
        if foods:
            best = None
            best_d2 = 1e18
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
                self._last_target = best

        friend_count_n = 0.0
        enemy_count_n = 0.0
        enemy_d_n = 1.0
        enemy_dx_n = 0.0
        enemy_dy_n = 0.0

        if agents:
            r2 = self.sight * self.sight
            friends = 0
            enemies = 0
            best_e = None
            best_e_d2 = 1e18
            for a in agents:
                if a is self:
                    continue
                ax = float(getattr(a, "x", 0.0))
                ay = float(getattr(a, "y", 0.0))
                d2 = _dist2(self.x, self.y, ax, ay)
                if d2 <= r2:
                    friends += 1
                if d2 < best_e_d2:
                    best_e_d2 = d2
                    best_e = (ax, ay)
                    enemies += 1
            friend_count_n = _clamp(friends / 10.0, 0.0, 1.0)
            enemy_count_n = _clamp(enemies / 10.0, 0.0, 1.0)
            if best_e is not None:
                dx = best_e[0] - self.x
                dy = best_e[1] - self.y
                d = math.sqrt(best_e_d2)
                enemy_d_n = _clamp(d / max(1e-9, self.sight), 0.0, 1.0)
                enemy_dx_n = _clamp(dx / max(1e-9, self.sight), -1.0, 1.0)
                enemy_dy_n = _clamp(dy / max(1e-9, self.sight), -1.0, 1.0)

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
            friend_count_n,
            enemy_count_n,
            enemy_d_n,
            enemy_dx_n,
            enemy_dy_n,
            1.0,
        ]

    def think(self, inputs):
        out = [0.0 for _ in range(self.output_size)]
        for i in range(self.input_size):
            xi = inputs[i]
            wi = self.W[i]
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

    def _move(self, turn: float, intensity: float):
        turn_delta = turn * (self.agility * 0.5)
        new_angle = self.angle + turn_delta

        inten = _clamp(0.5 + 0.5 * intensity, 0.0, 1.0)
        sp = self.base_speed * (0.20 + 1.30 * inten)

        rad = math.radians(new_angle)
        new_x = self.x + math.cos(rad) * sp
        new_y = self.y - math.sin(rad) * sp
        self._apply_bounds(new_x, new_y, new_angle)

        cost = 0.02 + 0.06 * inten
        self.energy = max(0.0, self.energy - cost)

    def _idle(self):
        self.energy = min(self.max_energy, self.energy + 0.03)

    def _flee(self, turn: float, intensity: float):
        if self._last_target is None:
            self._move(turn, intensity)
            return
        tx, ty = self._last_target
        dx = self.x - float(tx)
        dy = self.y - float(ty)
        ang = math.degrees(math.atan2(-dy, dx))
        self.angle = ang % 360.0
        self._move(0.0, max(0.2, intensity))

    def _attack(self):
        self.energy = max(0.0, self.energy - 0.08)

    def _mate(self):
        self.energy = max(0.0, self.energy - 0.05)

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

        if action == self.ACTION_MOVE:
            self._move(turn, intensity)
        elif action == self.ACTION_IDLE:
            self._idle()
        elif action == self.ACTION_FLEE:
            self._flee(turn, intensity)
        elif action == self.ACTION_MATE:
            self._mate()
        else:
            self._attack()

        self._tick_body()

    def render(self, window: pygame.window, cell_size: int, offset: tuple):
        offset_x, offset_y = offset

        env_x = offset_x + self.x * cell_size
        env_y = offset_y + self.y * cell_size

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
