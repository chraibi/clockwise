import math
import random
from dataclasses import dataclass

from .config import ArenaConfig


def carrot(pos: tuple[float, float], heading: float, distance: float) -> tuple[float, float]:
    """A steering target `distance` metres ahead of `pos` along `heading`."""
    return (pos[0] + distance * math.cos(heading), pos[1] + distance * math.sin(heading))


@dataclass
class Roamer:
    """Per-agent heading that random-walks, drifts CCW by the bias, and steers off the wall."""

    heading: float

    def update(
        self, pos: tuple[float, float], cfg: ArenaConfig, rng: random.Random
    ) -> float:
        h = self.heading + rng.gauss(0.0, cfg.wander_sigma) + cfg.bias_beta
        r = math.hypot(pos[0], pos[1])
        if r > cfg.radius - cfg.wall_margin and r > 0.0:
            inward = math.atan2(-pos[1], -pos[0])
            diff = math.atan2(math.sin(inward - h), math.cos(inward - h))
            h += cfg.wall_turn_gain * diff
        self.heading = h
        return h
