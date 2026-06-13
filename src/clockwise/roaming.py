import math
import random
from dataclasses import dataclass

from .config import ArenaConfig


def carrot(pos: tuple[float, float], heading: float, distance: float) -> tuple[float, float]:
    """A steering target `distance` metres ahead of `pos` along `heading`."""
    return (pos[0] + distance * math.cos(heading), pos[1] + distance * math.sin(heading))


def clamp_inside(
    point: tuple[float, float], radius: float, margin: float = 0.3
) -> tuple[float, float]:
    """Pull a point radially inward so it stays at least `margin` inside the disk rim."""
    r = math.hypot(point[0], point[1])
    lim = radius - margin
    if r > lim and r > 0.0:
        return (lim * point[0] / r, lim * point[1] / r)
    return point


@dataclass
class Roamer:
    """Per-agent heading: unbiased wander, an optional constant free-space curvature, and a
    wall response. Two ways to inject the individual bias:

    - `biased` (wall-turn study): turn LEFT only when facing the wall.
    - `free_curvature` (intrinsic study): a constant leftward turn applied EVERY step, so the
      agent veers continuously even far from any wall ("walking straight into circles").

    A `biased`/curvature-free agent that is neither turns symmetrically toward the centre at
    the wall — the control behaviour."""

    heading: float
    biased: bool = False
    free_curvature: float = 0.0

    def update(
        self, pos: tuple[float, float], cfg: ArenaConfig, rng: random.Random
    ) -> float:
        h = self.heading + rng.gauss(0.0, cfg.wander_sigma)  # unbiased wander
        h += self.free_curvature  # constant leftward veer (intrinsic bias; 0 in wall study)
        x, y = pos
        r = math.hypot(x, y)
        if r > cfg.radius - cfg.wall_margin and r > 0.0:
            phi_out = math.atan2(y, x)  # outward radial direction
            facing_out = math.cos(h - phi_out) > 0.0
            if self.biased:
                if facing_out:
                    h += cfg.left_wall_bias  # turn LEFT (CCW) away from the wall
            else:
                inward = math.atan2(-y, -x)  # symmetric turn toward the centre
                diff = math.atan2(math.sin(inward - h), math.cos(inward - h))
                h += cfg.wall_turn_gain * diff
        self.heading = h
        return h
