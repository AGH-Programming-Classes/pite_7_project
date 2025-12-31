import heapq
import math
import random
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from area import Area


AREA_COVERAGE: Dict[Area, float] = {
    Area.PLAINS: 0.4,
    Area.FERTILE_VALLEY: 0.25,
    Area.DESERT: 0.2,
    Area.BERRY_CORNER: 0.15,
}


ADJACENCY_WEIGHTS: Dict[Area, Dict[Area, float]] = {
    Area.PLAINS: {
        Area.PLAINS: 60,
        Area.FERTILE_VALLEY: 2,
        Area.DESERT: 1,
        Area.BERRY_CORNER: 1,
    },
    Area.FERTILE_VALLEY: {
        Area.PLAINS: 2,
        Area.FERTILE_VALLEY: 60,
        Area.DESERT: 1,
        Area.BERRY_CORNER: 1,
    },
    Area.DESERT: {
        Area.PLAINS: 1,
        Area.FERTILE_VALLEY: 1,
        Area.DESERT: 300,
        Area.BERRY_CORNER: 1,
    },
    Area.BERRY_CORNER: {
        Area.PLAINS: 1,
        Area.FERTILE_VALLEY: 2,
        Area.DESERT: 1,
        Area.BERRY_CORNER: 200,
    },
}


def generate_terrain(
    width: int,
    height: int,
    resolution: int,
    seed: Optional[int] = None,
    bias_min: float = 0.25,
    bias_max: float = 8.0,
) -> List[List[Area]]:
    """Single-function WFC-ish generator returning an Area grid."""
    assert width % resolution == 0 and height % resolution == 0
    grid_w = width // resolution
    grid_h = height // resolution

    rng = random.Random(seed)

    wave: List[List[Set[Area]]] = [
        [set(Area) for _ in range(grid_w)]
        for _ in range(grid_h)
    ]
    bias_grid: List[List[Dict[Area, float]]] = [
        [
            {area: 1.0 for area in Area}
            for _ in range(grid_w)
        ]
        for _ in range(grid_h)
    ]
    entropy_map: Dict[Tuple[int, int], float] = {}
    entropy_heap: List[Tuple[float, float, int, int]] = []
    unresolved = {
        (x, y)
        for y in range(grid_h)
        for x in range(grid_w)
    }
    terrain: List[List[Area]] = [
        [Area.PLAINS for _ in range(grid_w)] for _ in range(grid_h)
    ]

    def calculate_entropy(options: Sequence[Area], x: int, y: int) -> float:
        weights = [
            AREA_COVERAGE[area] * max(bias_grid[y][x][area], bias_min)
            for area in options
        ]
        total = sum(weights)
        if total <= 0:
            return 0.0
        probs = [w / total for w in weights]
        return -sum(p * math.log(p + 1e-12) for p in probs)

    def push_entropy(x: int, y: int) -> None:
        options = tuple(wave[y][x]) or tuple(Area)
        entropy = calculate_entropy(options, x, y)
        entropy_map[(x, y)] = entropy
        heapq.heappush(entropy_heap, (entropy, rng.random(), x, y))

    def pop_cell() -> Optional[Tuple[int, int]]:
        while entropy_heap:
            entropy, _, x, y = heapq.heappop(entropy_heap)
            if (x, y) not in unresolved:
                continue
            current = entropy_map.get((x, y))
            if current is None or abs(current - entropy) > 1e-9:
                continue
            return (x, y)
        return None

    def neighbours(x: int, y: int) -> Iterable[Tuple[int, int]]:
        if x > 0:
            yield (x - 1, y)
        if x + 1 < grid_w:
            yield (x + 1, y)
        if y > 0:
            yield (x, y - 1)
        if y + 1 < grid_h:
            yield (x, y + 1)

    for y in range(grid_h):
        for x in range(grid_w):
            push_entropy(x, y)

    while unresolved:
        cell = pop_cell()
        if cell is None:
            cell = next(iter(unresolved))
        x, y = cell

        options = list(wave[y][x]) or list(Area)
        weights = [
            AREA_COVERAGE[area] * max(bias_grid[y][x][area], bias_min)
            for area in options
        ]
        if not any(weights):
            weights = [AREA_COVERAGE[area] for area in options]
        chosen = rng.choices(options, weights=weights, k=1)[0]

        wave[y][x] = {chosen}
        terrain[y][x] = chosen
        bias_grid[y][x] = {
            area: 1.0 if area == chosen else 0.0 for area in Area
        }

        influence = ADJACENCY_WEIGHTS[chosen]
        for nx, ny in neighbours(x, y):
            if (nx, ny) not in unresolved:
                continue
            cell_bias = bias_grid[ny][nx]
            for candidate in Area:
                updated = cell_bias[candidate] * influence.get(candidate, 1.0)
                cell_bias[candidate] = max(
                    bias_min,
                    min(bias_max, updated),
                )
            push_entropy(nx, ny)

        unresolved.remove(cell)
        entropy_map.pop(cell, None)

    return terrain
