from agent import _clamp, dist2
from math import sqrt, atan2, radians, sin, cos, pi
from area import Area

class Sense:
    def __init__(self, parent):
        from agent import Agent
        self.parent : Agent = parent

    def get_agent_stats(self):
        hp_n = _clamp(self.parent.hp / max(1e-9, self.parent.max_hp), 0.0, 1.0)
        en_n = _clamp(self.parent.energy / max(1e-9, self.parent.max_energy), 0.0, 1.0)
        age_n = _clamp(self.parent.age / max(1, self.parent.max_age), 0.0, 1.0)
        return hp_n, en_n, age_n


    def object_cords_to_angle(self, x, y):
        dx = x - self.parent.x
        dy = y - self.parent.y
        angle_to_object = atan2(-dy, dx)
        return sin(angle_to_object), cos(angle_to_object)
    
    def get_closest_food(self, foods):
        if foods:
            best_d2 = 1e18
            best = None
            for f in foods:
                fx = float(getattr(f, "x", 0.0))
                fy = float(getattr(f, "y", 0.0))
                d2 = dist2(self.parent.x, self.parent.y, fx, fy)
                if d2 < best_d2:
                    best_d2 = d2
                    best = (fx, fy)
            food_sin, food_cos = self.object_cords_to_angle(*best)
            food_distance = _clamp(sqrt(best_d2)/max(self.parent.sight, 1e-9), 0, 1)
            food_in_sight = 1 if sqrt(best_d2) <= self.parent.sight else 0
        else:
            food_sin = 0
            food_cos = 0
            food_distance = 1
            food_in_sight = 0

        return food_sin, food_cos, food_distance, food_in_sight

    def get_close_agents(self, agents):
        from agent import Agent

        friend_count_n = 0
        friend_cord_sin = 0
        friend_cord_cos = 0
        friend_distance = 1
        friend_in_sight = 0

        enemy_count_n = 0
        enemy_cord_sin = 0
        enemy_cord_cos = 0
        enemy_distance = 1
        enemy_in_sight = 0
        if agents:
            r2 = self.parent.sight * self.parent.sight
            friends = 0
            enemies = 0
            best_friend_d2 = 1e18
            best_friend = None 
            best_enemy_d2 = 1e18
            best_enemy = None

            for a in agents:
                if a is self.parent:
                    continue
                ax = float(getattr(a, "x", 0.0))
                ay = float(getattr(a, "y", 0.0))
                d2 = dist2(self.parent.x, self.parent.y, ax, ay)
                if d2 > r2:
                    continue

                same_group = getattr(a, "group_id", None) == self.parent.group_id
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
                enemy_cord_sin, enemy_cord_cos = self.object_cords_to_angle(best_enemy[0], best_enemy[1])
                enemy_distance = _clamp( sqrt(best_enemy_d2) / max(self.parent.sight, 1e-9), 0, 1)
                enemy_in_sight = 1
            else:
                enemy_cord_sin = 0
                enemy_cord_cos = 0
                enemy_distance = 1
                enemy_in_sight = 0

            if best_friend is not None:
                friend_cord_sin, friend_cord_cos = self.object_cords_to_angle(best_friend[0], best_friend[1])
                friend_distance = _clamp( sqrt(best_friend_d2) / max(self.parent.sight, 1e-9), 0, 1)
                friend_in_sight = 1


        return friend_count_n, friend_cord_sin, friend_cord_cos, friend_distance, friend_in_sight, enemy_count_n, enemy_cord_sin, enemy_cord_cos, enemy_distance, enemy_in_sight
    
    def get_area_type(self):
        cell = self.parent.environment._get_agent_area(self.parent)
        if cell == Area.PLAINS: ground = 0
        elif cell == Area.FERTILE_VALLEY: ground = 0.9
        elif cell == Area.DESERT: ground = 0.1
        elif cell == Area.BERRY_CORNER: ground= 1
        else: raise ValueError(f"Wrong place! {cell}, {type(cell)}")
        return ground

    def sense(self, foods=None, agents=None ):


        hp_n, en_n, age_n = self.get_agent_stats()
        food_sin, food_cos, food_distance, food_in_sight = self.get_closest_food(foods)
        friend_count_n, friend_cord_sin, friend_cord_cos, friend_distance, friend_in_sight, enemy_count_n, enemy_cord_sin, enemy_cord_cos, enemy_distance, enemy_in_sight = self.get_close_agents(agents)
        area_type = self.get_area_type()


        return [
            hp_n,
            en_n,
            age_n,
            food_sin,
            food_cos,
            food_distance,
            food_in_sight,
            friend_count_n, 
            friend_cord_sin, 
            friend_cord_cos, 
            friend_distance, 
            friend_in_sight,
            enemy_count_n, 
            enemy_cord_sin, 
            enemy_cord_cos,
            enemy_distance, 
            enemy_in_sight,
            area_type,
            self.parent.last_action
        ]
